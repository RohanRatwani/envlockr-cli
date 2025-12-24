import argparse
import getpass
import json
import os
import stat
import sys

# Version
__version__ = "1.0.1"

# Try to import optional dependencies
pyperclip = None  # type: ignore
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    print("❌ Error: 'cryptography' package is required.")
    print("   Install it with: pip install cryptography")
    sys.exit(1)

# Constants
VAULT_DIR = os.path.expanduser("~/.envlockr")
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
def load_or_create_key():
    """Load existing key or create a new one"""
    ensure_vault_dir()
    
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        # Create key file with secure permissions
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if sys.platform != 'win32':
            fd = os.open(KEY_FILE, flags, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(key)
        else:
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
    else:
        try:
            with open(KEY_FILE, 'rb') as f:
                key = f.read()
        except PermissionError:
            print_error(f"Permission denied reading key file: {KEY_FILE}")
            sys.exit(1)
        except IOError as e:
            print_error(f"Error reading key file: {e}")
            sys.exit(1)
    
    try:
        return Fernet(key)
    except Exception:
        print_error("Invalid or corrupted key file.")
        print_info("You may need to delete ~/.envlockr/key.key and start fresh.")
        print_warning("WARNING: This will make existing secrets unrecoverable!")
        sys.exit(1)

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
    
    secret = getpass.getpass(prompt="Enter secret value: ")
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
    
    secret = getpass.getpass(prompt="Enter new secret value: ")
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

Documentation: https://github.com/RohanRatwani/envlockr-cli
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'EnvLockr v{__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    # Add
    add_parser = subparsers.add_parser('add', help='Add a new secret')
    add_parser.add_argument('name', help='Name of the secret (e.g., API_KEY)')
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

    args = parser.parse_args()
    
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
