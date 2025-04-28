
# 🔐 EnvLockr CLI

> Secure your environment variables — locally, encrypted, and stream-safe.

EnvLockr CLI is a tool for developers, streamers, and indie hackers who want full control of their secrets without relying on cloud services.

## ✨ Features

- **Local-first**: All secrets stored securely on your machine
- **AES Encryption**: Protects your secrets even if your disk is compromised
- **Offline Mode**: No internet needed to operate
- **Stream-Safe**: No .env file leaks on screen while coding or streaming
- **Simple CLI**: Add, copy, list, and retrieve secrets instantly
- **Cross-Project Friendly**: Works with React, Node.js, Python, and more

## 🚀 Quick Start

### 1. Install

```bash
# Quick installation
pip install cryptography pyperclip
```

Or manually:

```bash
git clone https://github.com/RohanRatwani/envlockr-cli.git
cd envlockr-cli
pip install -r requirements.txt
```

### 2. Commands

| Command | Example | What it Does |
|---------|---------|-------------|
| add | `python envlockr.py add STRIPE_KEY` | Add a new secret |
| get | `python envlockr.py get STRIPE_KEY` | Retrieve a secret |
| list | `python envlockr.py list` | List all stored secrets |
| copy | `python envlockr.py copy STRIPE_KEY` | Copy secret to clipboard |
## ⚡ How to Use in Your Projects

### 🖥 Node.js / React / Vite / Next.js

#### Option 1: Export to .env file

```bash
python envlockr.py export --output .env
npm run dev
```

#### Option 2: Inline Injection (no .env needed)

```bash
export STRIPE_KEY=$(python envlockr.py get STRIPE_KEY)
npm run dev
```

### 🛠 Compatible with

- create-react-app
- Next.js
- Vite
- Remix
- Express
- NestJS
- and more!

## 📦 Local Storage

All your secrets are encrypted and stored in:

```
~/.envlockr/vault.json
~/.envlockr/key.key
```

- ✅ AES-256 level security
- ✅ No external cloud or server dependency

## 💬 Why EnvLockr?

- 🔒 **Protect your keys** without trusting the cloud
- 🎥 **Stream coding sessions** without leaking environment secrets
- ⚡ **Speed up local development** with simple, fast secret management

## ☕ Support the Project

If you find EnvLockr useful, you can support its development by [becoming a sponsor](https://github.com/sponsors/RohanRatwani).

## 📥 Coming Soon

We are working on:

- Premium features like environment injection
- Project-specific vaults
- Desktop UI app

👉 [Join the Waitlist](https://forms.gle/example)

## 🛡 License

This project is licensed under the [MIT License](LICENSE).