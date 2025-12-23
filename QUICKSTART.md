# 🚀 EnvLockr Quick Reference

## Installation

```bash
pip install cryptography pyperclip
```

## Commands

### Add a Secret
```bash
python envlockr.py add API_KEY
# Prompts for secret value (hidden input)
```

### Get a Secret
```bash
python envlockr.py get API_KEY
# Outputs the secret value
```

### Copy to Clipboard
```bash
python envlockr.py copy API_KEY
# Secret copied! Paste anywhere
```

### List All Secrets
```bash
python envlockr.py list
# Shows all secret names (not values)
```

### Update a Secret
```bash
python envlockr.py update API_KEY
# Prompts for new value
```

### Delete a Secret
```bash
python envlockr.py delete API_KEY
# Removes the secret permanently
```

### Export to .env
```bash
python envlockr.py export
# Creates .env file with all secrets

python envlockr.py export --output config.env
# Custom output file
```

## Common Workflows

### React / Next.js / Vite

**Option 1: Export to .env**
```bash
python envlockr.py export
npm run dev
```

**Option 2: Inline (Unix/Mac)**
```bash
export API_KEY=$(python envlockr.py get API_KEY)
npm run dev
```

**Option 3: Inline (Windows PowerShell)**
```powershell
$env:API_KEY = python envlockr.py get API_KEY
npm run dev
```

### Python Projects

```python
import os
import subprocess

# Get secret from EnvLockr
api_key = subprocess.check_output(
    ['python', 'envlockr.py', 'get', 'API_KEY']
).decode().strip()

# Or use after export
python envlockr.py export
# Then use python-dotenv
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')
```

### Node.js / Express

```javascript
const { execSync } = require('child_process');

// Get secret from EnvLockr
const apiKey = execSync('python envlockr.py get API_KEY')
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
