# Changelog

All notable changes to EnvLockr will be documented in this file.

## [1.0.0] - 2025-10-11

### 🎉 Initial Release

#### Features
- **CLI Commands**: Add, get, list, copy, update, delete, and export secrets
- **AES-256 Encryption**: Military-grade encryption for local secret storage
- **Stream-Safe**: No .env files exposed during streaming or screen sharing
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **GitHub Action**: Automatic secret scanning for repositories
- **Zero Dependencies on Cloud**: Fully local and offline-capable

#### Security
- Local-first architecture
- Encrypted vault storage at `~/.envlockr/`
- No telemetry or data collection
- Open source and auditable

#### Documentation
- Complete README with examples
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
