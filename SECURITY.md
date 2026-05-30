# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅        |
| < 2.0   | ❌        |

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately via one of:

- GitHub's [private vulnerability reporting](https://github.com/RohanRatwani/envlockr-cli/security/advisories/new) (preferred)
- Email: **ratwani.rohan@gmail.com** with subject `[EnvLockr Security]`

Please include:

- A description of the issue and its impact
- Steps to reproduce (a minimal proof of concept if possible)
- Affected version(s)

You can expect an acknowledgement within **72 hours** and a status update within
**7 days**. Coordinated disclosure is appreciated — we will credit you in the
release notes unless you prefer to remain anonymous.

## Security Model (what EnvLockr does and does not protect)

EnvLockr is a **local-first** secrets manager. Its guarantees depend on how the
master key is stored:

- **With the `keychain` extra installed** (`pip install "envlockr[keychain]"`),
  the master key is stored in the OS keychain (Windows Credential Manager /
  macOS Keychain / libsecret) and never written to the filesystem. Reading
  `vault.json` alone does not reveal your secrets.
- **Without it**, the key falls back to a `0600` file at `~/.envlockr/key.key`
  next to the vault. In this mode, **anyone who can read your home directory can
  read your secrets** — the vault is encrypted at rest but the key sits beside it.
  EnvLockr warns you in this mode; run `envlockr secure-key` after installing the
  extra to migrate the key into the keychain.

Portable vaults created with `encrypt-vault` are protected by a password using
**PBKDF2-HMAC-SHA256 (600,000 iterations) with a random per-file salt**. The
strength of that protection is the strength of your password.

EnvLockr does **not** protect against:

- Malware or another user with read access to your account/keychain
- Secrets after they have been exported to a plaintext `.env` file
- Shoulder-surfing of values printed by `get`/`export`

Prefer `envlockr run -- <cmd>` over exporting a `.env` file when you can.
