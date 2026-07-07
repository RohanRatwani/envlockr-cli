# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in EnvLockr, please **do not** open a public GitHub issue.

Instead, report it via one of the following methods:

- **Email**: [security@envlockr.dev](mailto:security@envlockr.dev)
- **GitHub Private Advisory**: [Report a vulnerability](https://github.com/RohanRatwani/envlockr-cli/security/advisories/new)

Please include as much detail as possible:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

## What to Expect After Reporting

1. **Acknowledgement** – You will receive an acknowledgement within **48 hours**.
2. **Assessment** – We will investigate and assess the severity within **7 days**.
3. **Fix & Disclosure** – We aim to release a patch within **30 days** of confirmation. We will coordinate public disclosure with you and give credit where appropriate.

## Security Best Practices

### Vault Key File

EnvLockr stores your vault encryption key at `~/.envlockr/key.key`. To protect it:

- **Do not share or commit** the key file to version control.
- **Restrict file permissions**: The key file should be readable only by your user account. On Unix-based systems, EnvLockr sets permissions to `600` automatically. Verify this with:
  ```bash
  ls -la ~/.envlockr/key.key
  ```
- **Back up securely**: Store a backup of the key in a password manager or secure vault. Without the key, encrypted `.env` files cannot be decrypted.
- **Do not store in shared directories**: Avoid placing the key in directories accessible to other users or processes.
- **Rotate periodically**: Re-encrypt your vault with a fresh key if you suspect the key has been exposed.

### Encrypted Vault Files

- Encrypted `.env.vault` files are safe to commit to version control — they cannot be decrypted without the key.
- Never commit the **unencrypted** `.env` file to version control.
