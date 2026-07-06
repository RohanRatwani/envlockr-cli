# Changelog

All notable changes to EnvLockr will be documented in this file.

## [2.0.0] - 2026-05-30

### 🔐 Security

- **OS keychain master key** — when `envlockr[keychain]` is installed, the master
  key is stored in the OS keychain (Windows Credential Manager / macOS Keychain /
  libsecret) instead of a plaintext file beside the vault. Falls back to a `0600`
  key file with an explicit warning when no keychain is available.
- **`encrypt-vault` now uses a random per-file salt** (16 bytes) instead of a
  hard-coded shared salt, and bumps PBKDF2 from 100k to **600k** iterations.
  Old (v1) vault files remain decryptable via a legacy fallback path.
- Fixed a Windows `UnicodeEncodeError` crash when printing status glyphs on
  cp1252 consoles (stdout/stderr are now reconfigured to UTF-8).

### ✨ New Features

- **`envlockr run -- <cmd>`** — run any command with secrets injected into its
  environment. No `.env` file is written to disk. Supports `--only A,B`.
- **`envlockr verify [NAME]`** — liveness-check stored keys against their provider
  (Stripe, OpenAI, Anthropic, GitHub, Slack) to catch revoked or rotated keys.
- **`envlockr secure-key`** — migrate an existing on-disk key into the OS keychain.
- **Profiles** — `--env <name>` / `ENVLOCKR_ENV` for isolated per-environment
  vaults under `<base>/envs/<name>/`. The `default` profile is unchanged.

### 🛠 Tooling & Project

- Secret-scan GitHub Action now uses **gitleaks** when available, falling back to
  the built-in regex scanner otherwise.
- Added a cross-platform (Ubuntu/macOS/Windows × Python 3.8–3.12) test CI workflow.
- Test suite is now part of the repository (previously git-ignored); added tests
  for `run`, `verify`, profiles, and the new salted vault format.
- Fixed the placeholder maintainer email in package metadata.

### ⚠️ Breaking

- Major version bump. Behaviour is backward-compatible for existing default-profile
  vaults and v1 encrypted-vault files, but the master-key location changes for new
  installs that have the `keychain` extra.

## [1.1.0] - 2026-03-06

### ✨ New Features

#### Project-Specific Vaults (`ENVLOCKR_HOME`)
- Set `ENVLOCKR_HOME` environment variable to use a custom vault directory
- Example: `export ENVLOCKR_HOME="./config/secrets"` for per-project secrets
- Falls back to `~/.envlockr` when unset

#### Vault Encryption & Sharing
- **`envlockr encrypt-vault`** — Password-protect your vault into a portable `.envlockr` file
- **`envlockr decrypt-vault`** — Restore a vault from a password-protected file
- **`envlockr export-vault`** — Export vault for team sharing (alias for encrypt-vault)
- **`envlockr import-vault`** — Import a shared vault file (alias for decrypt-vault)
- Uses PBKDF2 key derivation for password-based encryption
- Bundles both vault data and encryption key into one portable file

#### Documentation
- Removed "planned for future" notes from EXAMPLES.md — features are now live
- Updated README commands table with new commands
- Updated CLI help text with new commands and ENVLOCKR_HOME docs

---

## [1.0.1] - 2026-03-06

### 🔧 Improvements

#### GitHub Action
- Refactored workflow to call `scan-secrets.sh` directly (DRY, no more duplicated patterns)
- Added **`SCAN_MODE`** environment variable (`lenient` / `normal` / `strict`) to control scan sensitivity
- Added **`IGNORE_PATTERNS`** environment variable for comma-separated ignore list
- Patterns split into tiered groups: provider-specific (all modes), generic auth (normal), broad heuristics (strict)
- Bumped scanner to v1.1 with improved pattern coverage
- Fixed potential `set -e` failure when `GITHUB_BASE_REF` is unset
- Removed unnecessary Python setup step from workflow (scanner is pure bash)
- PR comment now wraps findings in a code block for readability

#### Documentation
- Expanded `GITHUB_ACTION.md` with full customization docs (scan mode table, ignore patterns)
- Updated detection list to tabular format

---

## [1.0.0] - 2025-12-23

### 🎉 Initial Release

#### Features
- **CLI Commands**: Add, get, list, copy, update, delete, export, and import secrets
- **PyPI Package**: Install with `pip install envlockr`
- **Import from .env**: Migrate existing .env files with `envlockr import`
- **Encrypted Storage**: Fernet (AES-128-CBC + HMAC-SHA256) authenticated encryption for local secret storage
- **Colored Output**: Beautiful terminal output with success/error/warning colors
- **Stream-Safe**: No .env files exposed during streaming or screen sharing
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **GitHub Action**: Automatic secret scanning for repositories
- **Zero Dependencies on Cloud**: Fully local and offline-capable

#### Security
- Local-first architecture
- Encrypted vault storage at `~/.envlockr/`
- Secure key file permissions (600 on Unix)
- Security warnings for insecure permissions
- No telemetry or data collection
- Open source and auditable

#### Developer Experience
- `--version` flag to check version
- `--force` flag for non-interactive scripts
- Helpful error messages with suggestions
- Graceful handling of corrupted files

#### Documentation
- Complete README with examples
- Quick Start guide
- Framework examples (React, Next.js, Python, etc.)
- GitHub Action setup guide
- Contributing guidelines
- MIT License

### What's Next?

Check out our roadmap in [GitHub Issues](https://github.com/RohanRatwani/envlockr-cli/issues) for upcoming features!

---

## Version Format

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)
