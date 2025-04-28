🔐 EnvLockr CLI
Secure your environment variables — locally, encrypted, and stream-safe.
Perfect for developers, streamers, and indie hackers who want full control of their secrets without relying on cloud services.

✨ Features
Local-first: All secrets stored securely on your machine

AES Encryption: Protects your secrets even if your disk is compromised

Offline Mode: No internet needed to operate

Stream-Safe: No .env file leaks on screen while coding or streaming

Simple CLI: Add, copy, list, and retrieve secrets instantly

Cross-Project Friendly: Works with React, Node.js, Python, and more

🚀 Quick Start
1. Install
bash
Copy
Edit
pip install cryptography pyperclip
Or manually:

bash
Copy
Edit
git clone https://github.com/your-username/envlockr-cli.git
cd envlockr-cli
pip install -r requirements.txt
2. Commands

Command Example	What it Does
python envlockr.py add STRIPE_KEY	Add a new secret
python envlockr.py get STRIPE_KEY	Retrieve a secret
python envlockr.py list	List all stored secrets
python envlockr.py copy STRIPE_KEY	Copy secret to clipboard
⚡ How to Use in Your Projects
🖥 Node.js / React / Vite / Next.js
Option 1: Export to .env file

bash
Copy
Edit
python envlockr.py export --output .env
npm run dev
Option 2: Inline Injection (no .env needed)

bash
Copy
Edit
export STRIPE_KEY=$(python envlockr.py get STRIPE_KEY)
npm run dev
🛠 Works with:
create-react-app

Next.js

Vite

Remix

Express

NestJS

and more!

📦 Local Storage
All your secrets are encrypted and stored in:

bash
Copy
Edit
~/.envlockr/vault.json
~/.envlockr/key.key
Both files are created automatically when you first add a secret.

✅ AES-256 level security
✅ No external cloud or server dependency

💬 Why EnvLockr?
🔒 Protect your keys without trusting the cloud.
🎥 Stream coding sessions without leaking environment secrets.
⚡ Speed up local development with simple, fast secret management.

☕ Support the Project
If you find EnvLockr useful, you can support its development:


📥 Want More?
We are working on:

Premium features like environment injection

Project-specific vaults

Desktop UI app

👉 Join the Waitlist

🛡 License
This project is licensed under the MIT License.