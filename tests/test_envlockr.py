#!/usr/bin/env python3
"""
Unit tests for EnvLockr CLI
Run with: python run_tests.py
"""

import json
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path to import envlockr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import envlockr


class TestEnvLockrSetup(unittest.TestCase):
    """Test setup and initialization"""
    
    def setUp(self):
        """Create a temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_vault_dir = envlockr.VAULT_DIR
        self.original_vault_file = envlockr.VAULT_FILE
        self.original_key_file = envlockr.KEY_FILE
        
        # Override paths to use temp directory
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")

        # Force on-disk key mode so tests are deterministic regardless of
        # whether an OS keychain is present on the host.
        self.original_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.KEYRING_AVAILABLE = False
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Restore original paths
        envlockr.VAULT_DIR = self.original_vault_dir
        envlockr.VAULT_FILE = self.original_vault_file
        envlockr.KEY_FILE = self.original_key_file
        envlockr.KEYRING_AVAILABLE = self.original_keyring
    
    def test_version_exists(self):
        """Test that version is defined"""
        self.assertIsNotNone(envlockr.__version__)
        self.assertRegex(envlockr.__version__, r'^\d+\.\d+\.\d+$')
    
    def test_load_or_create_key_creates_new_key(self):
        """Test that a new key is created if none exists"""
        self.assertFalse(os.path.exists(envlockr.KEY_FILE))
        fernet = envlockr.load_or_create_key()
        self.assertTrue(os.path.exists(envlockr.KEY_FILE))
        self.assertIsNotNone(fernet)
    
    def test_load_or_create_key_loads_existing_key(self):
        """Test that existing key is loaded"""
        # Create key first time
        fernet1 = envlockr.load_or_create_key()
        # Load key second time
        fernet2 = envlockr.load_or_create_key()
        
        # Both should work with same encrypted data
        test_data = b"test secret"
        encrypted = fernet1.encrypt(test_data)
        decrypted = fernet2.decrypt(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_load_vault_returns_empty_dict_if_no_file(self):
        """Test that empty dict is returned if vault doesn't exist"""
        vault = envlockr.load_vault()
        self.assertEqual(vault, {})
    
    def test_save_and_load_vault(self):
        """Test saving and loading vault"""
        test_vault = {"SECRET1": "encrypted1", "SECRET2": "encrypted2"}
        envlockr.save_vault(test_vault)
        loaded_vault = envlockr.load_vault()
        self.assertEqual(loaded_vault, test_vault)


class TestSecretOperations(unittest.TestCase):
    """Test secret add/get/update/delete operations"""
    
    def setUp(self):
        """Create a temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_vault_dir = envlockr.VAULT_DIR
        self.original_vault_file = envlockr.VAULT_FILE
        self.original_key_file = envlockr.KEY_FILE
        
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")

        self.original_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.KEYRING_AVAILABLE = False

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        envlockr.VAULT_DIR = self.original_vault_dir
        envlockr.VAULT_FILE = self.original_vault_file
        envlockr.KEY_FILE = self.original_key_file
        envlockr.KEYRING_AVAILABLE = self.original_keyring
    
    def test_add_secret(self):
        """Test adding a new secret"""
        args = MagicMock()
        args.name = "TEST_SECRET"
        args.force = False
        args.value = "my_secret_value"
        args.stdin = False

        with patch('sys.stdout', new=StringIO()):
            envlockr.add_secret(args)
        
        # Verify secret was added
        vault = envlockr.load_vault()
        self.assertIn("TEST_SECRET", vault)
        
        # Verify it can be decrypted
        fernet = envlockr.load_or_create_key()
        decrypted = fernet.decrypt(vault["TEST_SECRET"].encode()).decode()
        self.assertEqual(decrypted, "my_secret_value")
    
    def test_get_secret(self):
        """Test retrieving a secret"""
        # First add a secret
        args = MagicMock()
        args.name = "TEST_SECRET"
        args.force = False
        args.value = "my_secret_value"
        args.stdin = False

        with patch('sys.stdout', new=StringIO()):
            envlockr.add_secret(args)
        
        # Now get it
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            envlockr.get_secret(args)
            output = mock_stdout.getvalue().strip()
        
        self.assertEqual(output, "my_secret_value")
    
    def test_get_nonexistent_secret(self):
        """Test getting a secret that doesn't exist"""
        args = MagicMock()
        args.name = "NONEXISTENT"
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            envlockr.get_secret(args)
            output = mock_stdout.getvalue()
        
        self.assertIn("not found", output.lower())
    
    def test_list_secrets(self):
        """Test listing secrets"""
        # Add some secrets
        for name in ["SECRET1", "SECRET2", "SECRET3"]:
            args = MagicMock()
            args.name = name
            args.force = True
            args.value = "value"
            args.stdin = False
            with patch('sys.stdout', new=StringIO()):
                envlockr.add_secret(args)
        
        # List them
        args = MagicMock()
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            envlockr.list_secrets(args)
            output = mock_stdout.getvalue()
        
        self.assertIn("SECRET1", output)
        self.assertIn("SECRET2", output)
        self.assertIn("SECRET3", output)
    
    def test_list_empty_vault(self):
        """Test listing when no secrets exist"""
        args = MagicMock()
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            envlockr.list_secrets(args)
            output = mock_stdout.getvalue()
        
        self.assertIn("No secrets", output)
    
    @patch('builtins.input')
    def test_delete_secret(self, mock_input):
        """Test deleting a secret"""
        # First add a secret
        args = MagicMock()
        args.name = "TEST_SECRET"
        args.force = True
        args.value = "my_secret_value"
        args.stdin = False

        with patch('sys.stdout', new=StringIO()):
            envlockr.add_secret(args)
        
        # Verify it exists
        vault = envlockr.load_vault()
        self.assertIn("TEST_SECRET", vault)
        
        # Delete it
        mock_input.return_value = "y"
        with patch('sys.stdout', new=StringIO()):
            envlockr.delete_secret(args)
        
        # Verify it's gone
        vault = envlockr.load_vault()
        self.assertNotIn("TEST_SECRET", vault)
    
    def test_update_secret(self):
        """Test updating a secret"""
        # First add a secret
        args = MagicMock()
        args.name = "TEST_SECRET"
        args.force = True
        args.value = "original_value"
        args.stdin = False

        with patch('sys.stdout', new=StringIO()):
            envlockr.add_secret(args)

        # Update it
        args.value = "new_value"
        with patch('sys.stdout', new=StringIO()):
            envlockr.update_secret(args)
        
        # Verify the new value
        fernet = envlockr.load_or_create_key()
        vault = envlockr.load_vault()
        decrypted = fernet.decrypt(vault["TEST_SECRET"].encode()).decode()
        self.assertEqual(decrypted, "new_value")


class TestExportImport(unittest.TestCase):
    """Test export and import operations"""
    
    def setUp(self):
        """Create a temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_vault_dir = envlockr.VAULT_DIR
        self.original_vault_file = envlockr.VAULT_FILE
        self.original_key_file = envlockr.KEY_FILE
        
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")

        self.original_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.KEYRING_AVAILABLE = False

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        envlockr.VAULT_DIR = self.original_vault_dir
        envlockr.VAULT_FILE = self.original_vault_file
        envlockr.KEY_FILE = self.original_key_file
        envlockr.KEYRING_AVAILABLE = self.original_keyring
    
    @patch('builtins.input')
    def test_export_secrets(self, mock_input):
        """Test exporting secrets to .env file"""
        # Add some secrets
        secrets = {"API_KEY": "secret123", "DB_URL": "postgres://localhost"}

        for name, value in secrets.items():
            args = MagicMock()
            args.name = name
            args.force = True
            args.value = value
            args.stdin = False
            with patch('sys.stdout', new=StringIO()):
                envlockr.add_secret(args)
        
        # Export to file
        output_file = os.path.join(self.temp_dir, ".env")
        args = MagicMock()
        args.output = output_file
        args.force = True
        
        mock_input.return_value = "y"
        with patch('sys.stdout', new=StringIO()):
            envlockr.export_secrets(args)
        
        # Verify file contents
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertIn("API_KEY=secret123", content)
        self.assertIn("DB_URL=postgres://localhost", content)
    
    @patch('builtins.input')
    def test_import_secrets(self, mock_input):
        """Test importing secrets from .env file"""
        # Create a .env file
        env_file = os.path.join(self.temp_dir, ".env")
        with open(env_file, 'w') as f:
            f.write("# Comment line\n")
            f.write("API_KEY=imported_secret\n")
            f.write("DB_URL=postgres://localhost\n")
            f.write('QUOTED_VALUE="with spaces"\n')
        
        # Import it
        args = MagicMock()
        args.file = env_file
        args.force = True
        
        mock_input.return_value = "y"
        with patch('sys.stdout', new=StringIO()):
            envlockr.import_secrets(args)
        
        # Verify secrets were imported
        fernet = envlockr.load_or_create_key()
        vault = envlockr.load_vault()
        
        self.assertIn("API_KEY", vault)
        self.assertIn("DB_URL", vault)
        self.assertIn("QUOTED_VALUE", vault)
        
        # Verify values
        self.assertEqual(
            fernet.decrypt(vault["API_KEY"].encode()).decode(),
            "imported_secret"
        )
        self.assertEqual(
            fernet.decrypt(vault["QUOTED_VALUE"].encode()).decode(),
            "with spaces"
        )
    
    def test_import_nonexistent_file(self):
        """Test importing from a file that doesn't exist"""
        args = MagicMock()
        args.file = "/nonexistent/path/.env"
        args.force = False
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            envlockr.import_secrets(args)
            output = mock_stdout.getvalue()
        
        self.assertIn("not found", output.lower())


class TestDecryptSecret(unittest.TestCase):
    """Test the decrypt_secret helper function"""
    
    def setUp(self):
        """Create a temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_vault_dir = envlockr.VAULT_DIR
        self.original_vault_file = envlockr.VAULT_FILE
        self.original_key_file = envlockr.KEY_FILE
        
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")

        self.original_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.KEYRING_AVAILABLE = False

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        envlockr.VAULT_DIR = self.original_vault_dir
        envlockr.VAULT_FILE = self.original_vault_file
        envlockr.KEY_FILE = self.original_key_file
        envlockr.KEYRING_AVAILABLE = self.original_keyring
    
    def test_decrypt_valid_secret(self):
        """Test decrypting a valid encrypted secret"""
        fernet = envlockr.load_or_create_key()
        original = "my_secret_value"
        encrypted = fernet.encrypt(original.encode()).decode()
        
        decrypted = envlockr.decrypt_secret(fernet, encrypted)
        self.assertEqual(decrypted, original)
    
    def test_decrypt_invalid_secret(self):
        """Test decrypting invalid data returns None"""
        fernet = envlockr.load_or_create_key()
        
        with patch('sys.stdout', new=StringIO()):
            result = envlockr.decrypt_secret(fernet, "invalid_encrypted_data")
        
        self.assertIsNone(result)


class TestNonInteractiveInput(unittest.TestCase):
    """Test --value / --stdin secret input (no getpass hang on piped input)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig = (envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE)
        self.orig_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")
        envlockr.KEYRING_AVAILABLE = False

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE = self.orig
        envlockr.KEYRING_AVAILABLE = self.orig_keyring

    def test_add_with_value_flag(self):
        args = MagicMock(name="A", value="flagval", stdin=False, force=True)
        args.name = "A"
        with patch('sys.stdout', new=StringIO()):
            envlockr.add_secret(args)
        fernet = envlockr.load_or_create_key()
        vault = envlockr.load_vault()
        self.assertEqual(envlockr.decrypt_secret(fernet, vault["A"]), "flagval")

    def test_resolve_reads_piped_stdin_without_flag(self):
        """A non-TTY stdin must be read instead of blocking on getpass."""
        args = MagicMock(value=None, stdin=False)
        with patch('sys.stdin', new=StringIO("piped-secret\n")), \
             patch.object(envlockr.sys.stdin, 'isatty', return_value=False, create=True):
            # StringIO.isatty() returns False already; this is belt-and-suspenders.
            val = envlockr._resolve_secret_value(args, "prompt: ")
        self.assertEqual(val, "piped-secret")

    def test_resolve_uses_getpass_on_tty(self):
        args = MagicMock(value=None, stdin=False)
        fake_stdin = MagicMock()
        fake_stdin.isatty.return_value = True
        with patch('sys.stdin', fake_stdin), \
             patch('getpass.getpass', return_value="typed") as gp:
            val = envlockr._resolve_secret_value(args, "prompt: ")
        gp.assert_called_once()
        self.assertEqual(val, "typed")


class TestColors(unittest.TestCase):
    """Test color helper class"""
    
    def test_colors_defined(self):
        """Test that color codes are defined"""
        self.assertIsNotNone(envlockr.Colors.RED)
        self.assertIsNotNone(envlockr.Colors.GREEN)
        self.assertIsNotNone(envlockr.Colors.YELLOW)
        self.assertIsNotNone(envlockr.Colors.NC)
    
    def test_colors_disable(self):
        """Test that colors can be disabled"""
        # Save original values
        original_red = envlockr.Colors.RED
        
        # Disable colors
        envlockr.Colors.disable()
        
        # All colors should be empty strings
        self.assertEqual(envlockr.Colors.RED, '')
        self.assertEqual(envlockr.Colors.GREEN, '')
        self.assertEqual(envlockr.Colors.NC, '')
        
        # Restore (for other tests)
        envlockr.Colors.RED = original_red


class TestPasswordVault(unittest.TestCase):
    """Test password-based vault encryption (random salt + legacy fallback)."""

    def test_derive_key_random_salt_differs(self):
        """Same password + different salts must produce different keys."""
        k1 = envlockr._derive_key_from_password("hunter2", os.urandom(16))
        k2 = envlockr._derive_key_from_password("hunter2", os.urandom(16))
        self.assertNotEqual(k1, k2)

    def test_derive_key_is_deterministic_for_salt(self):
        """Same password + same salt must reproduce the same key."""
        salt = os.urandom(16)
        self.assertEqual(
            envlockr._derive_key_from_password("hunter2", salt),
            envlockr._derive_key_from_password("hunter2", salt),
        )

    def test_encrypt_decrypt_vault_roundtrip(self):
        """encrypt-vault then decrypt-vault should restore the original vault."""
        from cryptography.fernet import Fernet
        temp_dir = tempfile.mkdtemp()
        out_file = os.path.join(temp_dir, "vault.envlockr")
        orig_dir, orig_vault, orig_key = (
            envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE)
        orig_keyring = envlockr.KEYRING_AVAILABLE
        try:
            envlockr.VAULT_DIR = temp_dir
            envlockr.VAULT_FILE = os.path.join(temp_dir, "vault.json")
            envlockr.KEY_FILE = os.path.join(temp_dir, "key.key")
            envlockr.KEYRING_AVAILABLE = False

            key = Fernet.generate_key()
            with open(envlockr.KEY_FILE, 'wb') as f:
                f.write(key)
            with open(envlockr.VAULT_FILE, 'w') as f:
                json.dump({"API_KEY": "ciphertext"}, f)

            enc = MagicMock(password="pw", output=out_file)
            with patch('sys.stdout', new=StringIO()):
                envlockr.encrypt_vault_cmd(enc)

            # File must carry the v2 magic header + a non-fixed salt.
            with open(out_file, 'rb') as f:
                head = f.read(len(envlockr.VAULT_MAGIC) + 16)
            self.assertTrue(head.startswith(envlockr.VAULT_MAGIC))

            os.remove(envlockr.VAULT_FILE)
            os.remove(envlockr.KEY_FILE)

            dec = MagicMock(file=out_file, password="pw", force=True)
            with patch('sys.stdout', new=StringIO()):
                envlockr.decrypt_vault_cmd(dec)

            with open(envlockr.VAULT_FILE) as f:
                restored = json.load(f)
            self.assertEqual(restored, {"API_KEY": "ciphertext"})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE = (
                orig_dir, orig_vault, orig_key)
            envlockr.KEYRING_AVAILABLE = orig_keyring


class TestProfiles(unittest.TestCase):
    """Test --env profile path resolution."""

    def setUp(self):
        self.orig = (envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE)

    def tearDown(self):
        envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE = self.orig

    def test_default_profile_uses_base_root(self):
        envlockr.set_profile("default")
        self.assertEqual(envlockr.VAULT_DIR, envlockr.BASE_DIR)

    def test_named_profile_is_isolated(self):
        envlockr.set_profile("prod")
        self.assertEqual(
            envlockr.VAULT_DIR, os.path.join(envlockr.BASE_DIR, "envs", "prod"))
        self.assertNotEqual(envlockr.VAULT_DIR, envlockr.BASE_DIR)


class TestVerify(unittest.TestCase):
    """Test provider detection / liveness classification."""

    def test_detect_stripe(self):
        with patch.object(envlockr, '_http_status', return_value=200):
            provider, status = envlockr._detect_and_verify("sk_live_abc123", 5)
        self.assertEqual(provider, "Stripe")
        self.assertEqual(status, "live")

    def test_detect_openai_invalid(self):
        with patch.object(envlockr, '_http_status', return_value=401):
            provider, status = envlockr._detect_and_verify("sk-proj-xyz", 5)
        self.assertEqual(provider, "OpenAI")
        self.assertEqual(status, "invalid")

    def test_detect_anthropic_not_openai(self):
        """sk-ant- keys must route to Anthropic, not fall through to OpenAI."""
        with patch.object(envlockr, '_http_status', return_value=200):
            provider, status = envlockr._detect_and_verify("sk-ant-api03-xyz", 5)
        self.assertEqual(provider, "Anthropic")
        self.assertEqual(status, "live")

    def test_detect_github(self):
        with patch.object(envlockr, '_http_status', return_value=200):
            provider, status = envlockr._detect_and_verify("ghp_token", 5)
        self.assertEqual(provider, "GitHub")

    def test_unrecognized_provider(self):
        provider, status = envlockr._detect_and_verify("just-a-value", 5)
        self.assertIsNone(provider)
        self.assertEqual(status, "unknown")


class TestRunInjection(unittest.TestCase):
    """Test that `run` injects secrets into the child process environment."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig = (envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE)
        self.orig_keyring = envlockr.KEYRING_AVAILABLE
        envlockr.VAULT_DIR = self.temp_dir
        envlockr.VAULT_FILE = os.path.join(self.temp_dir, "vault.json")
        envlockr.KEY_FILE = os.path.join(self.temp_dir, "key.key")
        envlockr.KEYRING_AVAILABLE = False

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        envlockr.VAULT_DIR, envlockr.VAULT_FILE, envlockr.KEY_FILE = self.orig
        envlockr.KEYRING_AVAILABLE = self.orig_keyring

    def test_run_injects_secret_into_child_env(self):
        fernet = envlockr.load_or_create_key()
        vault = {"MY_KEY": fernet.encrypt(b"s3cr3t").decode()}
        envlockr.save_vault(vault)

        captured = {}

        def fake_run(cmd, env=None):
            captured['env'] = env
            captured['cmd'] = cmd
            return MagicMock(returncode=0)

        args = MagicMock(only=None, cmd=['--', 'echo', 'hi'])
        with patch('subprocess.run', side_effect=fake_run), \
             patch('sys.stdout', new=StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                envlockr.run_command(args)

        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(captured['env']['MY_KEY'], "s3cr3t")
        self.assertEqual(captured['cmd'], ['echo', 'hi'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
