# EnvLockr GitHub Actions

This directory contains GitHub Actions for EnvLockr.

## Secret Scanner Workflow

The `secret-scan.yml` workflow automatically scans your repository for exposed secrets.

### What it does:
- 🔍 Scans all commits for API keys, tokens, and passwords
- 🚫 Blocks PRs if secrets are detected
- 💬 Posts helpful comments with fix instructions
- ✅ Runs on every push and pull request

### Detected Secrets:
- AWS Access Keys
- Stripe API Keys
- GitHub Tokens
- Google API Keys
- OpenAI API Keys
- Slack Tokens
- Database Connection Strings
- Generic API keys and passwords
- And more!

## Scanner Script

The `scripts/scan-secrets.sh` script can be used standalone or in CI/CD pipelines.

### Standalone usage:

```bash
# Make executable
chmod +x .github/scripts/scan-secrets.sh

# Run scanner
./.github/scripts/scan-secrets.sh
```

### Use in other projects:

```bash
# Download and run
curl -sSL https://raw.githubusercontent.com/RohanRatwani/envlockr-cli/main/.github/scripts/scan-secrets.sh | bash
```

## Documentation

For full setup instructions, see [GITHUB_ACTION.md](../GITHUB_ACTION.md)
