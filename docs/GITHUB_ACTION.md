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

      - name: Run EnvLockr Secret Scanner
        id: scan
        run: |
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

| Provider | Pattern |
|---|---|
| AWS | Access Keys (`AKIA...`) |
| Stripe | Live & test API keys |
| GitHub | PATs, OAuth tokens, fine-grained PATs |
| Google | API keys, OAuth tokens |
| OpenAI | API keys (`sk-...`, `sk-proj-...`) |
| Slack | Bot, user, app, and XOXE tokens |
| DigitalOcean | Personal access tokens |
| Square | Access tokens & OAuth secrets |
| Databases | MongoDB, PostgreSQL, MySQL, Redis, RabbitMQ connection strings |
| TLS/SSL | Private keys (RSA, DSA, EC, OpenSSH) |
| Generic | Bearer tokens, access tokens, client secrets *(normal mode)* |
| Generic | API keys, passwords, secrets *(strict mode only)* |

## Customization

### Adjust sensitivity

Set the `SCAN_MODE` environment variable (or a repository variable `ENVLOCKR_SCAN_MODE`):

| Mode | Description |
|---|---|
| `lenient` | High-confidence, provider-specific patterns only — fewest false-positives |
| `normal` | Default — includes generic bearer/access-token patterns |
| `strict` | All patterns including generic password/secret/api-key heuristics |

```yaml
- name: Run EnvLockr Secret Scanner
  env:
    SCAN_MODE: "strict"   # strict | normal (default) | lenient
  run: |
    chmod +x .github/scripts/scan-secrets.sh
    ./.github/scripts/scan-secrets.sh
```

Or set a repository variable in **Settings → Variables → Actions**:

```
ENVLOCKR_SCAN_MODE = strict
```

### Ignore specific files

Pass a comma-separated glob list via the `IGNORE_PATTERNS` environment variable (or repository variable `ENVLOCKR_IGNORE_PATTERNS`):

```yaml
- name: Run EnvLockr Secret Scanner
  env:
    IGNORE_PATTERNS: "*.test.js,*.spec.ts,examples/*"
  run: |
    chmod +x .github/scripts/scan-secrets.sh
    ./.github/scripts/scan-secrets.sh
```

## Need help?

- 📖 [Full Documentation](https://github.com/RohanRatwani/envlockr-cli)
- 🐛 [Report Issues](https://github.com/RohanRatwani/envlockr-cli/issues)
- 💬 [Join Discussion](https://github.com/RohanRatwani/envlockr-cli/discussions)

