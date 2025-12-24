# Changelog

All notable changes to EnvLockr will be documented in this file.

## [1.0.0] - 2025-12-23

### 🎉 Initial Release

#### Features
- **CLI Commands**: Add, get, list, copy, update, delete, export, and import secrets
- **PyPI Package**: Install with `pip install envlockr`
- **Import from .env**: Migrate existing .env files with `envlockr import`
- **AES-256 Encryption**: Military-grade encryption for local secret storage
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
