# 🔐 EnvLockr GitHub Action

Automatically scan your repository for exposed secrets and API keys.

## Quick Setup

Add this workflow to your repository to prevent secret leaks:

### 1. Create the workflow file

Create `.github/workflows/envlockr-scan.yml` in your repository:

```yaml
name: EnvLockr Secret Scan

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches:
      - main
      - master

jobs:
  scan-secrets:
    runs-on: ubuntu-latest
    name: Scan for exposed secrets
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Run EnvLockr Secret Scanner
        id: scan
        run: |
          # Download EnvLockr scanner script
          curl -sSL https://raw.githubusercontent.com/RohanRatwani/envlockr-cli/main/.github/scripts/scan-secrets.sh -o scan-secrets.sh
          chmod +x scan-secrets.sh
          ./scan-secrets.sh
```

### 2. That's it!

The action will now:
- ✅ Scan all pull requests automatically
- ✅ Detect common API keys and secrets
- ✅ Block merges if secrets are found
- ✅ Post helpful comments with fix instructions

## What it detects

- AWS Access Keys
- Stripe API Keys
- GitHub Tokens
- Google API Keys
- OpenAI API Keys
- Slack Tokens
- Database Connection Strings
- Generic API keys and passwords
- And more!

## Customization

### Ignore specific files

Add to your workflow:

```yaml
env:
  IGNORE_PATTERNS: "*.test.js,*.spec.ts,examples/*"
```

### Adjust sensitivity

```yaml
env:
  SCAN_MODE: "strict"  # strict, normal, or lenient
```

## Need help?

- 📖 [Full Documentation](https://github.com/RohanRatwani/envlockr-cli)
- 🐛 [Report Issues](https://github.com/RohanRatwani/envlockr-cli/issues)
- 💬 [Join Discussion](https://github.com/RohanRatwani/envlockr-cli/discussions)
