# Recording the EnvLockr demo

Two ways to produce a demo for the README / launch posts. Both use a throwaway
vault directory so your real secrets are never touched.

## Option A — VHS (recommended, deterministic GIF)

[VHS](https://github.com/charmbracelet/vhs) turns the included `demo.tape` into a
clean GIF with no manual typing.

```bash
# install: brew install vhs   (or see the VHS repo for Linux/Windows)
vhs demo.tape          # → demo.gif
```

Then reference it at the top of the README:

```markdown
<p align="center"><img src="demo.gif" alt="EnvLockr demo" /></p>
```

## Option B — asciinema (terminal cast)

```bash
export ENVLOCKR_HOME=$(mktemp -d)     # throwaway vault
asciinema rec envlockr-demo.cast
```

Then run this sequence (the "money shots" in order):

```bash
# 1. Store a secret — encrypted, local
envlockr add OPENAI_API_KEY --value sk-demo-not-a-real-key --force
envlockr list

# 2. Run an app with secrets injected — no .env file on disk
envlockr run -- node -e "console.log('app sees:', process.env.OPENAI_API_KEY)"

# 3. Check which stored keys are still live with their provider
envlockr verify
```

Stop the recording (Ctrl-D) and upload with `asciinema upload envlockr-demo.cast`.

## What to emphasize

The differentiator is steps **2 and 3** — `run` (no `.env` ever hits disk) and
`verify` (is this key still live?). dotenvx / SOPS / gitleaks don't do those.
Lead the demo and the launch post with `verify`.
