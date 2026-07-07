# EnvLockr (npm wrapper)

> Secure your environment variables — locally, encrypted, and stream-safe.

This package is a thin Node wrapper for the **EnvLockr CLI**. The canonical
distribution is the Python package:

```bash
pip install "envlockr[keychain]"
```

Once installed, this wrapper lets you call `envlockr` from npm-centric
workflows (npx, package.json scripts):

```jsonc
// package.json
{
  "scripts": {
    "dev": "envlockr run -- next dev"
  }
}
```

## What EnvLockr does

- **Local-first**: secrets encrypted on your machine — no cloud, no account
- **OS keychain**: master key in Windows Credential Manager / macOS Keychain / libsecret
- **`envlockr run -- <cmd>`**: inject secrets into any process — no `.env` on disk
- **`envlockr verify`**: check whether stored API keys are still live (Stripe, OpenAI, Anthropic, GitHub, Slack)

Full docs: https://github.com/RohanRatwani/envlockr-cli

MIT © Rohan Ratwani
