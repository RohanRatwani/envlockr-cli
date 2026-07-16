import argparse
import base64
import getpass
import hashlib
import json
import os
import stat
import subprocess
import sys

# Version
__version__ = "2.0.0"

# Try to import optional dependencies
pyperclip = None  # type: ignore
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# OS keychain support (Windows Credential Manager / macOS Keychain / libsecret).
# When available, the master key lives in the keychain instead of a file on disk.
keyring = None  # type: ignore
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    print("❌ Error: 'cryptography' package is required.")
    print("   Install it with: pip install cryptography")
    sys.exit(1)

# Base directory — respect ENVLOCKR_HOME for project-specific vaults
BASE_DIR = os.environ.get("ENVLOCKR_HOME", os.path.expanduser("~/.envlockr"))

# Active vault paths. The "default" profile lives at the base root for backward
# compatibility; named profiles live under <base>/envs/<name>/. set_profile()
# resets these globals once the --env flag has been parsed.
VAULT_DIR = BASE_DIR
VAULT_FILE = os.path.join(VAULT_DIR, "vault.json")
KEY_FILE = os.path.join(VAULT_DIR, "key.key")

# Keychain identity for the master key
KEYRING_SERVICE = "envlockr"

# Password-based vault encryption (encrypt-vault / export-vault)
PBKDF2_ITERATIONS = 600_000  # OWASP 2023 floor for PBKDF2-HMAC-SHA256
VAULT_MAGIC = b"ELKV2\n"     # marks the salted v2 portable-vault format
LEGACY_SALT = b'envlockr-vault-salt'
LEGACY_ITERATIONS = 100_000


def set_profile(name):
    """Point the active vault paths at the given profile.

    The 'default' profile stays at the base root so existing vaults keep
    working untouched. Named profiles are isolated under <base>/envs/<name>/.
    """
    global VAULT_DIR, VAULT_FILE, KEY_FILE
    if name and name != "default":
        VAULT_DIR = os.path.join(BASE_DIR, "envs", name)
    else:
        VAULT_DIR = BASE_DIR
    VAULT_FILE = os.path.join(VAULT_DIR, "vault.json")
    KEY_FILE = os.path.join(VAULT_DIR, "key.key")

# Color support
class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color
    
    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY or Windows without color support)"""
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.CYAN = cls.BOLD = cls.NC = ''

# Ensure stdout/stderr can encode emoji/Unicode on Windows (cp1252 consoles
# otherwise raise UnicodeEncodeError on the ✅/❌/🔐 status glyphs).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

# Disable colors if not a TTY or on Windows without proper support
if not sys.stdout.isatty():
    Colors.disable()
elif sys.platform == 'win32':
    try:
        # Enable ANSI colors on Windows 10+
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.disable()


def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def print_error(message):
    """Print error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")


def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def print_info(message):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")


# Ensure the ~/.envlockr directory exists
def ensure_vault_dir():
    """Create vault directory with secure permissions"""
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR, mode=0o700)


def check_key_file_security():
    """Warn if key file has insecure permissions (Unix-like systems)"""
    if sys.platform == 'win32':
        return  # Windows handles permissions differently
    
    if os.path.exists(KEY_FILE):
        try:
            file_stat = os.stat(KEY_FILE)
            mode = file_stat.st_mode
            # Check if group or others have any permissions
            if mode & (stat.S_IRWXG | stat.S_IRWXO):
                print_warning(f"Key file '{KEY_FILE}' has insecure permissions!")
                print_warning("Run: chmod 600 ~/.envlockr/key.key")
        except OSError:
            pass


# Utilities
def _keyring_id():
    """Stable per-vault identity used as the keychain account name."""
    return f"key:{os.path.abspath(VAULT_DIR)}"


def _keyring_get_key():
    """Return the master key bytes from the OS keychain, or None."""
    if not KEYRING_AVAILABLE:
        return None
    try:
        stored = keyring.get_password(KEYRING_SERVICE, _keyring_id())
    except Exception:
        return None
    return stored.encode() if stored else None


def _keyring_set_key(key):
    """Store the master key bytes in the OS keychain. Returns True on success."""
    if not KEYRING_AVAILABLE:
        return False
    try:
        keyring.set_password(KEYRING_SERVICE, _keyring_id(), key.decode())
        return True
    except Exception as e:
        print_warning(f"Could not write to OS keychain: {e}")
        return False


def _write_key_file(key):
    """Write the master key to disk with secure (0600) permissions."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if sys.platform != 'win32':
        fd = os.open(KEY_FILE, flags, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
    else:
        with open(KEY_FILE, 'wb') as f:
            f.write(key)


def _make_fernet(key):
    """Build a Fernet instance, exiting cleanly on a corrupt key."""
    try:
        return Fernet(key)
    except Exception:
        print_error("Invalid or corrupted master key.")
        print_info("You may need to remove the key and start fresh.")
        print_warning("WARNING: This will make existing secrets unrecoverable!")
        sys.exit(1)


def load_or_create_key():
    """Load the master key, preferring the OS keychain over an on-disk file.

    Resolution order:
      1. OS keychain (no key material touches disk) — if a key is stored there.
      2. Legacy/on-disk key file (existing installs, or systems without keyring).
      3. Create a new key: into the keychain when available, else a 0600 file
         with an explicit warning about the weaker disk-compromise posture.
    """
    ensure_vault_dir()

    kr_key = _keyring_get_key()
    if kr_key:
        return _make_fernet(kr_key)

    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, 'rb') as f:
                key = f.read()
        except PermissionError:
            print_error(f"Permission denied reading key file: {KEY_FILE}")
            sys.exit(1)
        except IOError as e:
            print_error(f"Error reading key file: {e}")
            sys.exit(1)
        return _make_fernet(key)

    # No key anywhere — create one.
    key = Fernet.generate_key()
    if _keyring_set_key(key):
        print_info("Master key stored in your OS keychain (not on disk).")
    else:
        _write_key_file(key)
        if not KEYRING_AVAILABLE:
            print_warning("OS keychain support not installed — master key written to disk.")
            print_info("For disk-compromise protection install: pip install envlockr[keychain]")
    return _make_fernet(key)

def load_vault():
    """Load the encrypted vault from disk"""
    ensure_vault_dir()
    
    if not os.path.exists(VAULT_FILE):
        return {}
    
    try:
        with open(VAULT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print_error("Vault file is corrupted.")
        print_info("You may need to delete ~/.envlockr/vault.json and start fresh.")
        sys.exit(1)
    except PermissionError:
        print_error(f"Permission denied reading vault: {VAULT_FILE}")
        sys.exit(1)
    except IOError as e:
        print_error(f"Error reading vault: {e}")
        sys.exit(1)


def save_vault(vault):
    """Save the vault to disk"""
    ensure_vault_dir()
    
    try:
        with open(VAULT_FILE, 'w') as f:
            json.dump(vault, f, indent=4)
    except PermissionError:
        print_error(f"Permission denied writing to vault: {VAULT_FILE}")
        sys.exit(1)
    except IOError as e:
        print_error(f"Error saving vault: {e}")
        sys.exit(1)


def decrypt_secret(fernet, encrypted_value):
    """Safely decrypt a secret value"""
    try:
        return fernet.decrypt(encrypted_value.encode()).decode()
    except InvalidToken:
        print_error("Failed to decrypt secret. Key may have changed.")
        print_info("If you regenerated your key, existing secrets cannot be recovered.")
        return None
    except Exception as e:
        print_error(f"Decryption error: {e}")
        return None


# CLI Commands
def _resolve_secret_value(args, prompt):
    """Get a secret value from --value, --stdin, or an interactive prompt.

    Falls back to getpass only when attached to a TTY, so piping into the
    command (CI / scripts) never hangs waiting on console input.
    """
    if getattr(args, 'value', None) is not None:
        return args.value
    if getattr(args, 'stdin', False):
        return sys.stdin.readline().rstrip('\n')
    if not sys.stdin.isatty():
        # Piped input without --stdin: read it rather than blocking on getpass.
        return sys.stdin.readline().rstrip('\n')
    return getpass.getpass(prompt=prompt)


def add_secret(args):
    """Add a new secret to the vault"""
    fernet = load_or_create_key()
    vault = load_vault()

    if args.name in vault and not getattr(args, 'force', False):
        print_warning(f"Secret '{args.name}' already exists.")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print_info("Operation cancelled.")
            return
    
    secret = _resolve_secret_value(args, "Enter secret value: ")
    if not secret:
        print_error("Secret value cannot be empty.")
        return

    encrypted = fernet.encrypt(secret.encode()).decode()
    vault[args.name] = encrypted
    save_vault(vault)
    print_success(f"Secret '{args.name}' added successfully.")


def get_secret(args):
    """Retrieve and display a secret"""
    fernet = load_or_create_key()
    vault = load_vault()
    
    if args.name not in vault:
        print_error(f"Secret '{args.name}' not found.")
        print_info("Use 'envlockr list' to see available secrets.")
        return
    
    decrypted = decrypt_secret(fernet, vault[args.name])
    if decrypted is not None:
        print(decrypted)


def list_secrets(args):
    """List all stored secret names"""
    vault = load_vault()
    
    if not vault:
        print_info("No secrets stored yet.")
        print_info("Add your first secret: envlockr add MY_SECRET")
        return
    
    print(f"{Colors.CYAN}🔐 Stored Secrets ({len(vault)}){Colors.NC}")
    for name in sorted(vault.keys()):
        print(f"   {Colors.BOLD}•{Colors.NC} {name}")


def copy_secret(args):
    """Copy a secret to clipboard"""
    if not PYPERCLIP_AVAILABLE:
        print_error("Clipboard support not available.")
        print_info("Install pyperclip: pip install pyperclip")
        return
    
    fernet = load_or_create_key()
    vault = load_vault()
    
    if args.name not in vault:
        print_error(f"Secret '{args.name}' not found.")
        return
    
    decrypted = decrypt_secret(fernet, vault[args.name])
    if decrypted is not None:
        try:
            pyperclip.copy(decrypted)  # type: ignore[union-attr]
            print_success(f"Secret '{args.name}' copied to clipboard.")
        except Exception as e:
            print_error(f"Failed to copy to clipboard: {e}")
            print_info("Use 'envlockr get' to display the secret instead.")


def delete_secret(args):
    """Delete a secret from the vault"""
    vault = load_vault()
    
    if args.name not in vault:
        print_error(f"Secret '{args.name}' not found.")
        return
    
    if not getattr(args, 'force', False):
        response = input(f"Delete secret '{args.name}'? [y/N]: ").strip().lower()
        if response != 'y':
            print_info("Operation cancelled.")
            return
    
    del vault[args.name]
    save_vault(vault)
    print_success(f"Secret '{args.name}' deleted.")


def update_secret(args):
    """Update an existing secret"""
    fernet = load_or_create_key()
    vault = load_vault()
    
    if args.name not in vault:
        print_error(f"Secret '{args.name}' not found.")
        print_info("Use 'envlockr add' to create a new secret.")
        return
    
    secret = _resolve_secret_value(args, "Enter new secret value: ")
    if not secret:
        print_error("Secret value cannot be empty.")
        return

    encrypted = fernet.encrypt(secret.encode()).decode()
    vault[args.name] = encrypted
    save_vault(vault)
    print_success(f"Secret '{args.name}' updated.")


def export_secrets(args):
    """Export all secrets to a .env file"""
    fernet = load_or_create_key()
    vault = load_vault()
    
    if not vault:
        print_info("No secrets to export.")
        return
    
    output_file = args.output if args.output else ".env"
    
    # Check if file exists
    if os.path.exists(output_file) and not getattr(args, 'force', False):
        print_warning(f"File '{output_file}' already exists.")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print_info("Operation cancelled.")
            return
    
    try:
        exported_count = 0
        with open(output_file, 'w') as f:
            f.write(f"# Generated by EnvLockr v{__version__}\n")
            f.write(f"# {len(vault)} secrets exported\n\n")
            for name, encrypted_value in sorted(vault.items()):
                decrypted = decrypt_secret(fernet, encrypted_value)
                if decrypted is not None:
                    # Handle multi-line values and special characters
                    if '\n' in decrypted or '"' in decrypted:
                        f.write(f'{name}="{decrypted}"\n')
                    else:
                        f.write(f"{name}={decrypted}\n")
                    exported_count += 1
        
        print_success(f"Exported {exported_count} secrets to '{output_file}'")
        print_warning(f"Remember: Add '{output_file}' to .gitignore!")
    except PermissionError:
        print_error(f"Permission denied writing to '{output_file}'")
    except IOError as e:
        print_error(f"Error exporting secrets: {e}")


def import_secrets(args):
    """Import secrets from a .env file"""
    fernet = load_or_create_key()
    vault = load_vault()
    
    input_file = args.file
    
    if not os.path.exists(input_file):
        print_error(f"File '{input_file}' not found.")
        return
    
    try:
        imported = 0
        skipped = 0
        
        with open(input_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=value format
                if '=' not in line:
                    print_warning(f"Line {line_num}: Invalid format, skipping")
                    skipped += 1
                    continue
                
                # Split on first = only (value may contain =)
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                if not key:
                    print_warning(f"Line {line_num}: Empty key, skipping")
                    skipped += 1
                    continue
                
                # Check for existing secret
                if key in vault and not getattr(args, 'force', False):
                    print_warning(f"Secret '{key}' already exists, skipping (use --force to overwrite)")
                    skipped += 1
                    continue
                
                # Encrypt and store
                encrypted = fernet.encrypt(value.encode()).decode()
                vault[key] = encrypted
                imported += 1
        
        save_vault(vault)
        print_success(f"Imported {imported} secrets from '{input_file}'")
        if skipped > 0:
            print_info(f"Skipped {skipped} entries")
        print_warning(f"Consider deleting '{input_file}' now that secrets are secure!")
        
    except PermissionError:
        print_error(f"Permission denied reading '{input_file}'")
    except IOError as e:
        print_error(f"Error reading file: {e}")


def _derive_key_from_password(password, salt, iterations=PBKDF2_ITERATIONS):
    """Derive a Fernet key from a password + salt using PBKDF2-HMAC-SHA256."""
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    return base64.urlsafe_b64encode(key)


def encrypt_vault_cmd(args):
    """Encrypt the vault file with a password for portability"""
    if not os.path.exists(VAULT_FILE):
        print_error("No vault found to encrypt.")
        return

    password = args.password
    if not password:
        password = getpass.getpass(prompt="Enter password to encrypt vault: ")
        confirm = getpass.getpass(prompt="Confirm password: ")
        if password != confirm:
            print_error("Passwords do not match.")
            return

    if not password:
        print_error("Password cannot be empty.")
        return

    try:
        with open(VAULT_FILE, 'r') as f:
            vault_data = f.read()
        with open(KEY_FILE, 'rb') as f:
            key_data = f.read()
    except (IOError, FileNotFoundError) as e:
        print_error(f"Error reading vault files: {e}")
        return

    # Bundle vault + key into one payload and encrypt with password
    bundle = json.dumps({
        "vault": vault_data,
        "key": base64.b64encode(key_data).decode()
    })

    # Random per-file salt (v2 format): MAGIC || 16-byte salt || Fernet token.
    salt = os.urandom(16)
    fernet = Fernet(_derive_key_from_password(password, salt))
    token = fernet.encrypt(bundle.encode())

    output_file = getattr(args, 'output', None) or "vault.envlockr"
    try:
        with open(output_file, 'wb') as f:
            f.write(VAULT_MAGIC + salt + token)
        print_success(f"Vault encrypted to '{output_file}'")
        print_info("Share this file safely — it requires the password to decrypt.")
    except IOError as e:
        print_error(f"Error writing encrypted vault: {e}")


def decrypt_vault_cmd(args):
    """Decrypt a password-protected vault file and restore it"""
    input_file = getattr(args, 'file', None) or "vault.envlockr"

    if not os.path.exists(input_file):
        print_error(f"File '{input_file}' not found.")
        return

    password = args.password
    if not password:
        password = getpass.getpass(prompt="Enter password to decrypt vault: ")

    if not password:
        print_error("Password cannot be empty.")
        return

    try:
        with open(input_file, 'rb') as f:
            data = f.read()
    except IOError as e:
        print_error(f"Error reading file: {e}")
        return

    # v2 format carries a random salt header; legacy files used a fixed salt.
    if data.startswith(VAULT_MAGIC):
        salt = data[len(VAULT_MAGIC):len(VAULT_MAGIC) + 16]
        token = data[len(VAULT_MAGIC) + 16:]
        derived = _derive_key_from_password(password, salt)
    else:
        token = data
        derived = _derive_key_from_password(password, LEGACY_SALT, LEGACY_ITERATIONS)

    try:
        fernet = Fernet(derived)
        decrypted = fernet.decrypt(token).decode()
    except InvalidToken:
        print_error("Wrong password or corrupted file.")
        return

    bundle = json.loads(decrypted)

    # Check for existing vault
    if os.path.exists(VAULT_FILE) and not getattr(args, 'force', False):
        print_warning("A vault already exists at this location.")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print_info("Operation cancelled.")
            return

    ensure_vault_dir()

    try:
        with open(VAULT_FILE, 'w') as f:
            f.write(bundle["vault"])
        key_bytes = base64.b64decode(bundle["key"])
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if sys.platform != 'win32':
            fd = os.open(KEY_FILE, flags, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(key_bytes)
        else:
            with open(KEY_FILE, 'wb') as f:
                f.write(key_bytes)
        print_success("Vault restored successfully.")
    except IOError as e:
        print_error(f"Error restoring vault: {e}")


def export_vault_cmd(args):
    """Export vault as a password-encrypted portable file"""
    # Alias for encrypt-vault with --output
    encrypt_vault_cmd(args)


def import_vault_cmd(args):
    """Import a password-encrypted vault file"""
    # Alias for decrypt-vault with --file
    decrypt_vault_cmd(args)


def secure_key_cmd(args):
    """Migrate an on-disk master key into the OS keychain."""
    if not KEYRING_AVAILABLE:
        print_error("OS keychain support not installed.")
        print_info("Install it with: pip install envlockr[keychain]")
        return

    if _keyring_get_key():
        print_info("Master key is already stored in the OS keychain.")
        return

    if not os.path.exists(KEY_FILE):
        print_error("No on-disk key file found to migrate.")
        return

    try:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    except IOError as e:
        print_error(f"Error reading key file: {e}")
        return

    # Validate before we touch anything.
    _make_fernet(key)

    if not _keyring_set_key(key):
        print_error("Failed to store key in OS keychain.")
        return

    print_success("Master key moved into the OS keychain.")
    if not getattr(args, 'force', False):
        response = input(f"Delete on-disk key file '{KEY_FILE}'? [y/N]: ").strip().lower()
        if response != 'y':
            print_warning("Key file kept on disk — remove it manually for full protection.")
            return
    try:
        os.remove(KEY_FILE)
        print_success("On-disk key file removed. Key now lives only in the keychain.")
    except OSError as e:
        print_error(f"Could not remove key file: {e}")


def run_command(args):
    """Run a command with secrets injected into its environment (no .env on disk)."""
    if not args.cmd:
        print_error("No command given.")
        print_info("Usage: envlockr run -- <command> [args...]")
        sys.exit(1)

    # argparse.REMAINDER keeps a leading '--'; drop it so the child sees a clean argv.
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == '--' else args.cmd
    if not cmd:
        print_error("No command given after '--'.")
        sys.exit(1)

    fernet = load_or_create_key()
    vault = load_vault()

    if not vault:
        print_warning("No secrets stored — running command with the current environment.")

    if getattr(args, 'only', None):
        wanted = [n.strip() for n in args.only.split(',') if n.strip()]
    else:
        wanted = list(vault.keys())

    child_env = os.environ.copy()
    injected = 0
    for name in wanted:
        if name not in vault:
            print_warning(f"Secret '{name}' not found, skipping.")
            continue
        decrypted = decrypt_secret(fernet, vault[name])
        if decrypted is not None:
            child_env[name] = decrypted
            injected += 1

    # Diagnostic goes to stderr so it never pollutes the child's stdout
    # (e.g. `envlockr run -- cmd > out`).
    print(f"{Colors.BLUE}ℹ️  Injecting {injected} secret(s) into: "
          f"{' '.join(cmd)}{Colors.NC}", file=sys.stderr)
    try:
        completed = subprocess.run(cmd, env=child_env)
        sys.exit(completed.returncode)
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        sys.exit(127)


# --- Liveness verification ---------------------------------------------------
# Detects the provider from the secret's value and makes one lightweight
# authenticated request to see whether the key is still live. Uses only the
# stdlib (urllib) so no extra dependency is required.

def _http_status(url, headers, timeout):
    """Return the HTTP status code for a GET request, or None on network error."""
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def _detect_and_verify(value, timeout):
    """Return (provider, status) where status is 'live', 'invalid', or 'unknown'."""
    def classify(code):
        if code is None:
            return 'unknown'
        if code in (200, 201, 204):
            return 'live'
        if code in (401, 403):
            return 'invalid'
        return 'unknown'

    if value.startswith(('sk_live_', 'sk_test_', 'rk_live_', 'rk_test_')):
        token = base64.b64encode(f"{value}:".encode()).decode()
        code = _http_status("https://api.stripe.com/v1/balance",
                            {"Authorization": f"Basic {token}"}, timeout)
        return ('Stripe', classify(code))

    if value.startswith('sk-ant-'):
        code = _http_status("https://api.anthropic.com/v1/models",
                            {"x-api-key": value,
                             "anthropic-version": "2023-06-01"}, timeout)
        return ('Anthropic', classify(code))

    if value.startswith(('sk-', 'sk-proj-')):
        code = _http_status("https://api.openai.com/v1/models",
                            {"Authorization": f"Bearer {value}"}, timeout)
        return ('OpenAI', classify(code))

    if value.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'github_pat_')):
        code = _http_status("https://api.github.com/user",
                            {"Authorization": f"Bearer {value}",
                             "User-Agent": "envlockr"}, timeout)
        return ('GitHub', classify(code))

    if value.startswith(('xoxb-', 'xoxp-', 'xoxa-')):
        code = _http_status("https://slack.com/api/auth.test",
                            {"Authorization": f"Bearer {value}"}, timeout)
        # Slack always returns 200; body carries ok:true/false, so treat 200 as reachable.
        return ('Slack', 'unknown' if code != 200 else 'live')

    if value.startswith('dop_v1_'):
        code = _http_status("https://api.digitalocean.com/v2/account",
                            {"Authorization" : f"Bearer {value}"},timeout)
        return ('DigitalOcean',classify(code))

    return (None, 'unknown')


def verify_command(args):
    """Check whether stored secrets are still live with their provider."""
    fernet = load_or_create_key()
    vault = load_vault()

    if not vault:
        print_info("No secrets stored yet.")
        return

    if getattr(args, 'name', None):
        if args.name not in vault:
            print_error(f"Secret '{args.name}' not found.")
            return
        names = [args.name]
    else:
        names = sorted(vault.keys())

    timeout = getattr(args, 'timeout', 5) or 5
    print_info("Checking key liveness (network required)...")
    icons = {'live': '🟢', 'invalid': '🔴', 'unknown': '⚪'}
    labels = {'live': 'live', 'invalid': 'INVALID/revoked', 'unknown': 'unknown provider'}

    for name in names:
        decrypted = decrypt_secret(fernet, vault[name])
        if decrypted is None:
            continue
        provider, status = _detect_and_verify(decrypted, timeout)
        prov = provider or 'unrecognized'
        print(f"   {icons[status]} {Colors.BOLD}{name}{Colors.NC} "
              f"({prov}): {labels[status]}")


def main():
    """Main entry point for EnvLockr CLI"""
    parser = argparse.ArgumentParser(
        description="EnvLockr CLI - Secure Local Secrets Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  envlockr add API_KEY          Add a new secret
  envlockr get API_KEY          Retrieve a secret
  envlockr copy API_KEY         Copy secret to clipboard
  envlockr list                 List all secrets
  envlockr export               Export to .env file
  envlockr import .env          Import from .env file
  envlockr run -- npm run dev   Run a command with secrets injected (no .env)
  envlockr verify               Check whether stored keys are still live
  envlockr encrypt-vault        Password-protect your vault
  envlockr decrypt-vault        Restore a password-protected vault
  envlockr export-vault         Export vault for team sharing
  envlockr import-vault         Import a shared vault file
  envlockr secure-key           Move the master key into your OS keychain
  envlockr --env prod list      Use a named, isolated profile

Environment:
  ENVLOCKR_HOME                 Custom vault directory (default: ~/.envlockr)
  ENVLOCKR_ENV                  Default profile name (default: default)

Documentation: https://github.com/RohanRatwani/envlockr-cli
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'EnvLockr v{__version__}'
    )
    parser.add_argument(
        '--env', '-e',
        default=os.environ.get("ENVLOCKR_ENV", "default"),
        metavar='PROFILE',
        help='Vault profile to use (default: "default")'
    )

    subparsers = parser.add_subparsers(dest='command', metavar='command')

    # Add
    add_parser = subparsers.add_parser('add', help='Add a new secret')
    add_parser.add_argument('name', help='Name of the secret (e.g., API_KEY)')
    add_parser.add_argument('--value', '-V', default=None, help='Secret value (non-interactive; avoid in shared shells/history)')
    add_parser.add_argument('--stdin', action='store_true', help='Read the secret value from stdin')
    add_parser.add_argument('--force', '-f', action='store_true', help='Overwrite without confirmation')
    add_parser.set_defaults(func=add_secret)

    # Get
    get_parser = subparsers.add_parser('get', help='Retrieve a secret (prints to stdout)')
    get_parser.add_argument('name', help='Name of the secret')
    get_parser.set_defaults(func=get_secret)

    # List
    list_parser = subparsers.add_parser('list', help='List all stored secrets')
    list_parser.set_defaults(func=list_secrets)

    # Copy
    copy_parser = subparsers.add_parser('copy', help='Copy a secret to clipboard')
    copy_parser.add_argument('name', help='Name of the secret')
    copy_parser.set_defaults(func=copy_secret)

    # Delete
    delete_parser = subparsers.add_parser('delete', help='Delete a secret')
    delete_parser.add_argument('name', help='Name of the secret')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Delete without confirmation')
    delete_parser.set_defaults(func=delete_secret)

    # Update
    update_parser = subparsers.add_parser('update', help='Update an existing secret')
    update_parser.add_argument('name', help='Name of the secret')
    update_parser.add_argument('--value', '-V', default=None, help='New secret value (non-interactive)')
    update_parser.add_argument('--stdin', action='store_true', help='Read the new value from stdin')
    update_parser.set_defaults(func=update_secret)

    # Export
    export_parser = subparsers.add_parser('export', help='Export secrets to .env file')
    export_parser.add_argument('--output', '-o', default='.env', help='Output file path (default: .env)')
    export_parser.add_argument('--force', '-f', action='store_true', help='Overwrite without confirmation')
    export_parser.set_defaults(func=export_secrets)

    # Import
    import_parser = subparsers.add_parser('import', help='Import secrets from .env file')
    import_parser.add_argument('file', help='Path to .env file to import')
    import_parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing secrets')
    import_parser.set_defaults(func=import_secrets)

    # Encrypt Vault
    enc_parser = subparsers.add_parser('encrypt-vault', help='Password-protect your vault for backup/sharing')
    enc_parser.add_argument('--password', '-p', default=None, help='Encryption password (prompted if omitted)')
    enc_parser.add_argument('--output', '-o', default='vault.envlockr', help='Output file (default: vault.envlockr)')
    enc_parser.set_defaults(func=encrypt_vault_cmd)

    # Decrypt Vault
    dec_parser = subparsers.add_parser('decrypt-vault', help='Restore a password-protected vault')
    dec_parser.add_argument('--file', default='vault.envlockr', help='Encrypted vault file (default: vault.envlockr)')
    dec_parser.add_argument('--password', '-p', default=None, help='Decryption password (prompted if omitted)')
    dec_parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing vault without confirmation')
    dec_parser.set_defaults(func=decrypt_vault_cmd)

    # Export Vault (alias for encrypt-vault)
    expv_parser = subparsers.add_parser('export-vault', help='Export vault as encrypted file for team sharing')
    expv_parser.add_argument('--password', '-p', default=None, help='Encryption password (prompted if omitted)')
    expv_parser.add_argument('--output', '-o', default='vault.envlockr', help='Output file (default: vault.envlockr)')
    expv_parser.set_defaults(func=export_vault_cmd)

    # Import Vault (alias for decrypt-vault)
    impv_parser = subparsers.add_parser('import-vault', help='Import an encrypted vault file from a teammate')
    impv_parser.add_argument('--file', default='vault.envlockr', help='Encrypted vault file (default: vault.envlockr)')
    impv_parser.add_argument('--password', '-p', default=None, help='Decryption password (prompted if omitted)')
    impv_parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing vault without confirmation')
    impv_parser.set_defaults(func=import_vault_cmd)

    # Run (inject secrets into a subprocess — no .env file touches disk)
    run_parser = subparsers.add_parser('run', help='Run a command with secrets injected into its environment')
    run_parser.add_argument('--only', default=None, help='Comma-separated subset of secrets to inject (default: all)')
    run_parser.add_argument('cmd', nargs=argparse.REMAINDER, help='Command to run, after "--" (e.g. run -- npm run dev)')
    run_parser.set_defaults(func=run_command)

    # Verify (liveness check against the provider)
    verify_parser = subparsers.add_parser('verify', help='Check whether stored keys are still live')
    verify_parser.add_argument('name', nargs='?', default=None, help='Verify a single secret (default: all)')
    verify_parser.add_argument('--timeout', '-t', type=float, default=5, help='Per-request timeout in seconds (default: 5)')
    verify_parser.set_defaults(func=verify_command)

    # Secure key (migrate on-disk key into the OS keychain)
    sk_parser = subparsers.add_parser('secure-key', help='Move the master key into your OS keychain')
    sk_parser.add_argument('--force', '-f', action='store_true', help='Delete the on-disk key file without confirmation')
    sk_parser.set_defaults(func=secure_key_cmd)

    args = parser.parse_args()

    # Resolve the active profile before any vault/key access.
    set_profile(getattr(args, 'env', 'default'))

    # Check key file security on startup
    check_key_file_security()

    if hasattr(args, 'func'):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n")
            print_info("Operation cancelled.")
            sys.exit(0)
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            print_info("Please report this issue at: https://github.com/RohanRatwani/envlockr-cli/issues")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
