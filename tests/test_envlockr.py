"""Tests for EnvLockr CLI core functionality."""

import argparse
import base64
import json
import os
import subprocess
import sys

import pytest
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    """Point every test at a fresh, temporary vault directory."""
    monkeypatch.setenv("ENVLOCKR_HOME", str(tmp_path))
    import envlockr

    monkeypatch.setattr(envlockr, "VAULT_DIR", str(tmp_path))
    monkeypatch.setattr(envlockr, "VAULT_FILE", str(tmp_path / "vault.json"))
    monkeypatch.setattr(envlockr, "KEY_FILE", str(tmp_path / "key.key"))
    yield tmp_path


def _run_cli(*args):
    """Run envlockr.py as a subprocess (non-interactive commands only)."""
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "..", "envlockr.py")] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=15,
        env={**os.environ},
    )
    return result.returncode, result.stdout, result.stderr


def _add_secret_directly(name, value):
    """Add a secret by calling the envlockr API directly (avoids getpass)."""
    import envlockr

    fernet = envlockr.load_or_create_key()
    vault = envlockr.load_vault()
    vault[name] = fernet.encrypt(value.encode()).decode()
    envlockr.save_vault(vault)


# ---------------------------------------------------------------------------
# Unit tests – encryption helpers
# ---------------------------------------------------------------------------


class TestEncryptionHelpers:
    def test_load_or_create_key_creates_key_file(self, isolated_vault):
        import envlockr

        fernet = envlockr.load_or_create_key()
        assert os.path.exists(envlockr.KEY_FILE)
        assert fernet is not None

    def test_load_or_create_key_returns_same_key(self, isolated_vault):
        import envlockr

        f1 = envlockr.load_or_create_key()
        f2 = envlockr.load_or_create_key()
        # Encrypt with f1, decrypt with f2 – must round-trip
        token = f1.encrypt(b"hello")
        assert f2.decrypt(token) == b"hello"

    def test_decrypt_secret_success(self, isolated_vault):
        import envlockr

        fernet = envlockr.load_or_create_key()
        encrypted = fernet.encrypt(b"my-secret-value").decode()
        assert envlockr.decrypt_secret(fernet, encrypted) == "my-secret-value"

    def test_decrypt_secret_wrong_key(self, isolated_vault, capsys):
        import envlockr

        other_fernet = Fernet(Fernet.generate_key())
        encrypted = other_fernet.encrypt(b"value").decode()

        fernet = envlockr.load_or_create_key()
        result = envlockr.decrypt_secret(fernet, encrypted)
        assert result is None
        captured = capsys.readouterr()
        assert "decrypt" in captured.out.lower() or "key" in captured.out.lower()

    def test_derive_key_from_password_deterministic(self):
        import envlockr

        k1 = envlockr._derive_key_from_password("password123")
        k2 = envlockr._derive_key_from_password("password123")
        assert k1 == k2

    def test_derive_key_from_password_different_passwords(self):
        import envlockr

        k1 = envlockr._derive_key_from_password("password1")
        k2 = envlockr._derive_key_from_password("password2")
        assert k1 != k2


# ---------------------------------------------------------------------------
# Unit tests – vault load / save
# ---------------------------------------------------------------------------


class TestVaultOperations:
    def test_load_vault_empty(self, isolated_vault):
        import envlockr

        vault = envlockr.load_vault()
        assert vault == {}

    def test_save_and_load_vault(self, isolated_vault):
        import envlockr

        envlockr.save_vault({"KEY": "encrypted_value"})
        vault = envlockr.load_vault()
        assert vault == {"KEY": "encrypted_value"}

    def test_vault_file_created_on_save(self, isolated_vault):
        import envlockr

        envlockr.save_vault({"A": "B"})
        assert os.path.exists(envlockr.VAULT_FILE)

    def test_ensure_vault_dir_creates_directory(self, tmp_path):
        import envlockr

        sub = str(tmp_path / "nested" / "vault")
        envlockr.VAULT_DIR = sub
        envlockr.ensure_vault_dir()
        assert os.path.isdir(sub)


# ---------------------------------------------------------------------------
# CLI integration tests – via subprocess
# ---------------------------------------------------------------------------


class TestCLI:
    def test_help(self, isolated_vault):
        rc, out, _ = _run_cli("--help")
        assert rc == 0
        assert "EnvLockr" in out

    def test_version(self, isolated_vault):
        import envlockr

        rc, out, _ = _run_cli("--version")
        assert rc == 0
        assert envlockr.__version__ in out

    def test_list_empty(self, isolated_vault):
        rc, out, _ = _run_cli("list")
        assert rc == 0
        assert "No secrets" in out

    def test_add_and_get(self, isolated_vault, monkeypatch):
        import envlockr

        monkeypatch.setattr("getpass.getpass", lambda prompt="": "secret123")
        args = argparse.Namespace(name="MY_KEY", force=False)
        envlockr.add_secret(args)

        rc, out, _ = _run_cli("get", "MY_KEY")
        assert rc == 0
        assert "secret123" in out

    def test_add_and_list(self, isolated_vault):
        _add_secret_directly("KEY_A", "val_a")
        _add_secret_directly("KEY_B", "val_b")
        rc, out, _ = _run_cli("list")
        assert rc == 0
        assert "KEY_A" in out
        assert "KEY_B" in out

    def test_delete_force(self, isolated_vault):
        _add_secret_directly("DEL_KEY", "todelete")
        rc, out, _ = _run_cli("delete", "DEL_KEY", "--force")
        assert rc == 0
        assert "deleted" in out.lower()

        # Verify it's gone
        rc, out, _ = _run_cli("get", "DEL_KEY")
        assert "not found" in out.lower()

    def test_get_nonexistent(self, isolated_vault):
        rc, out, _ = _run_cli("get", "NOPE")
        assert "not found" in out.lower()

    def test_update_existing(self, isolated_vault, monkeypatch):
        import envlockr

        _add_secret_directly("UPD_KEY", "old_val")
        monkeypatch.setattr("getpass.getpass", lambda prompt="": "new_val")
        args = argparse.Namespace(name="UPD_KEY")
        envlockr.update_secret(args)

        rc, out, _ = _run_cli("get", "UPD_KEY")
        assert rc == 0
        assert "new_val" in out

    def test_update_nonexistent(self, isolated_vault, monkeypatch, capsys):
        import envlockr

        monkeypatch.setattr("getpass.getpass", lambda prompt="": "val")
        args = argparse.Namespace(name="NOPE")
        envlockr.update_secret(args)
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_export_empty(self, isolated_vault):
        rc, out, _ = _run_cli("export", "--output", str(isolated_vault / "out.env"))
        assert rc == 0
        assert "no secrets" in out.lower()

    def test_export_and_import(self, isolated_vault):
        _add_secret_directly("EXP_KEY", "exp_val")

        env_file = str(isolated_vault / "exported.env")
        rc, out, _ = _run_cli("export", "--output", env_file)
        assert rc == 0
        assert os.path.exists(env_file)

        # Delete existing and reimport
        _run_cli("delete", "EXP_KEY", "--force")
        rc, out, _ = _run_cli("import", env_file, "--force")
        assert rc == 0
        assert "imported" in out.lower()

        # Verify round-trip
        rc, out, _ = _run_cli("get", "EXP_KEY")
        assert "exp_val" in out

    def test_import_nonexistent_file(self, isolated_vault):
        rc, out, _ = _run_cli("import", "/no/such/file.env")
        assert "not found" in out.lower()


# ---------------------------------------------------------------------------
# CLI integration tests – vault encrypt / decrypt
# ---------------------------------------------------------------------------


class TestVaultEncryptDecrypt:
    def test_encrypt_no_vault(self, isolated_vault, capsys):
        import envlockr

        args = argparse.Namespace(password="pw", output="vault.envlockr")
        envlockr.encrypt_vault_cmd(args)
        captured = capsys.readouterr()
        assert "no vault" in captured.out.lower()

    def test_encrypt_and_decrypt_round_trip(self, isolated_vault):
        _add_secret_directly("ROUND", "tripval")

        enc_file = str(isolated_vault / "vault.envlockr")
        rc, out, _ = _run_cli("encrypt-vault", "--password", "testpw", "--output", enc_file)
        assert rc == 0
        assert os.path.exists(enc_file)

        # Wipe original vault
        os.remove(os.path.join(str(isolated_vault), "vault.json"))
        os.remove(os.path.join(str(isolated_vault), "key.key"))

        # Decrypt
        rc, out, _ = _run_cli("decrypt-vault", "--password", "testpw", "--file", enc_file, "--force")
        assert rc == 0
        assert "restored" in out.lower()

        # Verify secret survived
        rc, out, _ = _run_cli("get", "ROUND")
        assert "tripval" in out

    def test_decrypt_wrong_password(self, isolated_vault):
        _add_secret_directly("WP", "v")
        enc_file = str(isolated_vault / "vault.envlockr")
        _run_cli("encrypt-vault", "--password", "right", "--output", enc_file)

        rc, out, _ = _run_cli("decrypt-vault", "--password", "wrong", "--file", enc_file, "--force")
        assert "wrong password" in out.lower() or "corrupted" in out.lower()


# ---------------------------------------------------------------------------
# CLI subcommand help smoke tests
# ---------------------------------------------------------------------------


class TestSubcommandHelp:
    @pytest.mark.parametrize(
        "cmd",
        [
            "add",
            "get",
            "list",
            "copy",
            "delete",
            "update",
            "export",
            "import",
            "encrypt-vault",
            "decrypt-vault",
            "export-vault",
            "import-vault",
        ],
    )
    def test_subcommand_help(self, cmd, isolated_vault):
        rc, out, _ = _run_cli(cmd, "--help")
        assert rc == 0
