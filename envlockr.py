import argparse
import getpass
import json
import os
import subprocess
import sys
import pyperclip
from cryptography.fernet import Fernet

# Constants
VAULT_FILE = os.path.expanduser("~/.envlockr/vault.json")
KEY_FILE = os.path.expanduser("~/.envlockr/key.key")

# Ensure the ~/.envlockr directory exists
os.makedirs(os.path.dirname(VAULT_FILE), exist_ok=True)

# Utilities
def load_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    return Fernet(key)

def load_vault():
    if not os.path.exists(VAULT_FILE):
        return {}
    with open(VAULT_FILE, 'r') as f:
        return json.load(f)

def save_vault(vault):
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

# CLI Commands
def add_secret(args):
    fernet = load_or_create_key()
    vault = load_vault()
    secret = getpass.getpass(prompt="Enter secret value: ")
    encrypted = fernet.encrypt(secret.encode()).decode()
    vault[args.name] = encrypted
    save_vault(vault)
    print(f"✅ Secret '{args.name}' added successfully.")

def get_secret(args):
    fernet = load_or_create_key()
    vault = load_vault()
    if args.name not in vault:
        print("❌ Secret not found.")
        return
    decrypted = fernet.decrypt(vault[args.name].encode()).decode()
    print(decrypted)

def list_secrets(args):
    vault = load_vault()
    if not vault:
        print("ℹ️ No secrets stored yet.")
        return
    print("🔐 Stored Secrets:")
    for name in vault:
        print(f" - {name}")

def copy_secret(args):
    fernet = load_or_create_key()
    vault = load_vault()
    if args.name not in vault:
        print("❌ Secret not found.")
        return
    decrypted = fernet.decrypt(vault[args.name].encode()).decode()
    pyperclip.copy(decrypted)
    print(f"📋 Secret '{args.name}' copied to clipboard.")

def delete_secret(args):
    vault = load_vault()
    if args.name not in vault:
        print("❌ Secret not found.")
        return
    del vault[args.name]
    save_vault(vault)
    print(f"🗑️ Secret '{args.name}' deleted successfully.")

def update_secret(args):
    fernet = load_or_create_key()
    vault = load_vault()
    if args.name not in vault:
        print(f"❌ Secret '{args.name}' not found. Use 'add' to create a new secret.")
        return
    secret = getpass.getpass(prompt="Enter new secret value: ")
    encrypted = fernet.encrypt(secret.encode()).decode()
    vault[args.name] = encrypted
    save_vault(vault)
    print(f"✅ Secret '{args.name}' updated successfully.")

def export_secrets(args):
    fernet = load_or_create_key()
    vault = load_vault()
    if not vault:
        print("ℹ️ No secrets to export.")
        return
    
    output_file = args.output if args.output else ".env"
    
    try:
        with open(output_file, 'w') as f:
            for name, encrypted_value in vault.items():
                decrypted = fernet.decrypt(encrypted_value.encode()).decode()
                f.write(f"{name}={decrypted}\n")
        print(f"✅ Secrets exported to '{output_file}'")
        print(f"⚠️  Remember: Add '{output_file}' to .gitignore to prevent leaks!")
    except Exception as e:
        print(f"❌ Error exporting secrets: {e}")

def main():
    parser = argparse.ArgumentParser(description="EnvLockr CLI - Secure Local Secrets Manager")
    subparsers = parser.add_subparsers()

    # Add
    add_parser = subparsers.add_parser('add', help='Add a new secret')
    add_parser.add_argument('name', help='Name of the secret')
    add_parser.set_defaults(func=add_secret)

    # Get
    get_parser = subparsers.add_parser('get', help='Retrieve a secret')
    get_parser.add_argument('name', help='Name of the secret')
    get_parser.set_defaults(func=get_secret)

    # List
    list_parser = subparsers.add_parser('list', help='List all stored secrets')
    list_parser.set_defaults(func=list_secrets)

    # Copy
    copy_parser = subparsers.add_parser('copy', help='Copy a secret to clipboard')
    copy_parser.add_argument('name', help='Name of the secret')
    copy_parser.set_defaults(func=copy_secret)

    # Delete
    delete_parser = subparsers.add_parser('delete', help='Delete a secret')
    delete_parser.add_argument('name', help='Name of the secret')
    delete_parser.set_defaults(func=delete_secret)

    # Update
    update_parser = subparsers.add_parser('update', help='Update an existing secret')
    update_parser.add_argument('name', help='Name of the secret')
    update_parser.set_defaults(func=update_secret)

    # Export
    export_parser = subparsers.add_parser('export', help='Export secrets to .env file')
    export_parser.add_argument('--output', '-o', default='.env', help='Output file path (default: .env)')
    export_parser.set_defaults(func=export_secrets)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
