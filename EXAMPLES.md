# 📖 EnvLockr Framework Examples

Real-world examples of using EnvLockr with popular frameworks.

## Table of Contents

- [React](#react)
- [Next.js](#nextjs)
- [Vite](#vite)
- [Node.js/Express](#nodejsexpress)
- [Python/Flask](#pythonflask)
- [Python/Django](#pythondjango)
- [Docker](#docker)
- [GitHub Actions](#github-actions)

---

## React

### Create React App

```bash
# Store your secrets
python envlockr.py add REACT_APP_API_URL
python envlockr.py add REACT_APP_API_KEY

# Export to .env
python envlockr.py export

# Start your app
npm start
```

**In your code:**
```javascript
// src/config.js
const config = {
  apiUrl: process.env.REACT_APP_API_URL,
  apiKey: process.env.REACT_APP_API_KEY,
};

export default config;
```

---

## Next.js

```bash
# Store secrets
python envlockr.py add NEXT_PUBLIC_API_URL
python envlockr.py add DATABASE_URL
python envlockr.py add JWT_SECRET

# Export
python envlockr.py export

# Run dev server
npm run dev
```

**Server-side usage:**
```javascript
// pages/api/data.js
export default async function handler(req, res) {
  const dbUrl = process.env.DATABASE_URL;
  const jwtSecret = process.env.JWT_SECRET;
  
  // Your logic here
}
```

**Client-side usage:**
```javascript
// components/App.js
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

---

## Vite

```bash
# Store secrets (must start with VITE_)
python envlockr.py add VITE_API_URL
python envlockr.py add VITE_API_KEY

# Export
python envlockr.py export

# Run dev
npm run dev
```

**In your code:**
```javascript
// src/config.js
export const config = {
  apiUrl: import.meta.env.VITE_API_URL,
  apiKey: import.meta.env.VITE_API_KEY,
};
```

---

## Node.js/Express

### Method 1: Using .env file

```bash
# Store secrets
python envlockr.py add PORT
python envlockr.py add DATABASE_URL
python envlockr.py add JWT_SECRET

# Export
python envlockr.py export

# Run app
node server.js
```

**server.js:**
```javascript
require('dotenv').config();
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;
const dbUrl = process.env.DATABASE_URL;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Method 2: Direct retrieval

```javascript
// config.js
const { execSync } = require('child_process');

function getSecret(name) {
  return execSync(`python envlockr.py get ${name}`)
    .toString()
    .trim();
}

module.exports = {
  port: getSecret('PORT'),
  dbUrl: getSecret('DATABASE_URL'),
  jwtSecret: getSecret('JWT_SECRET'),
};
```

---

## Python/Flask

### Method 1: Using .env

```bash
# Store secrets
python envlockr.py add FLASK_SECRET_KEY
python envlockr.py add DATABASE_URL
python envlockr.py add API_KEY

# Export
python envlockr.py export
```

**app.py:**
```python
from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

@app.route('/')
def index():
    api_key = os.getenv('API_KEY')
    return 'Hello World'

if __name__ == '__main__':
    app.run()
```

### Method 2: Direct retrieval

```python
import subprocess

def get_secret(name):
    result = subprocess.run(
        ['python', 'envlockr.py', 'get', name],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Usage
SECRET_KEY = get_secret('FLASK_SECRET_KEY')
```

---

## Python/Django

```bash
# Store secrets
python envlockr.py add DJANGO_SECRET_KEY
python envlockr.py add DATABASE_URL
python envlockr.py add AWS_ACCESS_KEY_ID
python envlockr.py add AWS_SECRET_ACCESS_KEY

# Export
python envlockr.py export
```

**settings.py:**
```python
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_URL'),
    }
}

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
```

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.9

WORKDIR /app

# Install EnvLockr
RUN pip install cryptography pyperclip

# Copy EnvLockr files
COPY envlockr.py .
COPY .envlockr /root/.envlockr/

# Export secrets at build time
RUN python envlockr.py export --output .env

# Your app setup
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
    command: sh -c "python envlockr.py export && python app.py"
```

---

## GitHub Actions

### Workflow with EnvLockr secrets

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Install EnvLockr
        run: pip install cryptography pyperclip
      
      - name: Add secrets to EnvLockr
        run: |
          echo "${{ secrets.API_KEY }}" | python envlockr.py add API_KEY
          echo "${{ secrets.DATABASE_URL }}" | python envlockr.py add DATABASE_URL
      
      - name: Export and deploy
        run: |
          python envlockr.py export
          # Your deployment commands here
```

---

## CI/CD Best Practices

### Option 1: Store encrypted vault in repo

```bash
# Encrypt vault with a master password
# (Add this feature in future version)
python envlockr.py encrypt-vault --password $MASTER_PASSWORD

# In CI/CD, decrypt and use
python envlockr.py decrypt-vault --password $MASTER_PASSWORD
python envlockr.py export
```

### Option 2: Use CI/CD secrets + EnvLockr for local dev

**Local development:**
```bash
python envlockr.py add API_KEY
npm run dev
```

**CI/CD (GitHub Actions):**
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

---

## Tips & Tricks

### 1. Project-specific .envlockr directory

```bash
# Store vault in project directory
export ENVLOCKR_HOME="./config/secrets"
python envlockr.py add SECRET
```

### 2. Team sharing (encrypted)

```bash
# Export vault for team member
python envlockr.py export-vault --encrypt --password "team-password"

# Team member imports
python envlockr.py import-vault --decrypt --password "team-password"
```

*Note: These features are planned for future releases*

### 3. Backup your secrets

```bash
# Backup vault
cp -r ~/.envlockr ~/Backups/envlockr-backup-$(date +%Y%m%d)

# Or use cloud storage (encrypted)
tar -czf envlockr-backup.tar.gz ~/.envlockr
# Upload to encrypted cloud storage
```

---

## Need Help?

- 📖 [Main Documentation](README.md)
- 🚀 [Quick Start Guide](QUICKSTART.md)
- 💬 [GitHub Discussions](https://github.com/RohanRatwani/envlockr-cli/discussions)
