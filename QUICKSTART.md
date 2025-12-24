# 🚀 EnvLockr Quick Reference

## Installation

```bash
# From PyPI (recommended)
pip install envlockr

# With clipboard support
pip install envlockr[clipboard]
```

## Commands

### Add a Secret
```bash
envlockr add API_KEY
# Prompts for secret value (hidden input)
```

### Get a Secret
```bash
envlockr get API_KEY
# Outputs the secret value
```

### Copy to Clipboard
```bash
envlockr copy API_KEY
# Secret copied! Paste anywhere
```

### List All Secrets
```bash
envlockr list
# Shows all secret names (not values)
```

### Update a Secret
```bash
envlockr update API_KEY
# Prompts for new value
```

### Delete a Secret
```bash
envlockr delete API_KEY
# Removes the secret permanently
```

### Export to .env
```bash
envlockr export
# Creates .env file with all secrets

envlockr export --output config.env
# Custom output file
```

### Import from .env
```bash
envlockr import .env
# Import existing secrets from .env file

envlockr import .env --force
# Overwrite existing secrets
```

### Check Version
```bash
envlockr --version
# Shows current version
```

## Common Workflows

### React / Next.js / Vite

**Option 1: Export to .env**
```bash
envlockr export
npm run dev
```

**Option 2: Inline (Unix/Mac)**
```bash
export API_KEY=$(envlockr get API_KEY)
npm run dev
```

**Option 3: Inline (Windows PowerShell)**
```powershell
$env:API_KEY = envlockr get API_KEY
npm run dev
```

**Option 4: Migrate existing .env**
```bash
envlockr import .env
rm .env  # Delete unencrypted file
```

### Python Projects

```python
import os
import subprocess

# Get secret from EnvLockr
api_key = subprocess.check_output(
    ['envlockr', 'get', 'API_KEY']
).decode().strip()

# Or use after export
# envlockr export
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')
```

### Node.js / Express

```javascript
const { execSync } = require('child_process');

// Get secret from EnvLockr
const apiKey = execSync('envlockr get API_KEY')
  .toString()
  .trim();

// Or use after export with dotenv
require('dotenv').config();
const apiKey = process.env.API_KEY;
```

## Security Tips

✅ **Do:**
- Store secrets in EnvLockr
- Add `.env` to `.gitignore`
- Use environment variables in code
- Rotate secrets regularly

❌ **Don't:**
- Commit `.env` files
- Hardcode secrets in source code
- Share `~/.envlockr/key.key`
- Use production secrets in development

## File Locations

- **Vault**: `~/.envlockr/vault.json` (encrypted)
- **Key**: `~/.envlockr/key.key` (keep safe!)

## Need Help?

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/RohanRatwani/envlockr-cli/issues)
- 💬 [Discussions](https://github.com/RohanRatwani/envlockr-cli/discussions)
- 🌐 [Website](https://envlockr.netlify.app)
