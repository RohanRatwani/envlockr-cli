#!/usr/bin/env node
// EnvLockr npm wrapper — proxies to the Python CLI (the canonical distribution).
// If the CLI isn't installed, prints install instructions instead.
'use strict';

const { spawnSync } = require('child_process');

const args = process.argv.slice(2);

// 1) envlockr on PATH (pip install puts it there)
let result = spawnSync('envlockr', args, { stdio: 'inherit', shell: false });
if (!result.error) {
  process.exit(result.status === null ? 1 : result.status);
}

// 2) fall back to `python -m envlockr`
for (const py of ['python3', 'python']) {
  result = spawnSync(py, ['-m', 'envlockr', ...args], { stdio: 'inherit', shell: false });
  if (!result.error && result.status !== 9009) {
    process.exit(result.status === null ? 1 : result.status);
  }
}

console.error(`
EnvLockr CLI not found.

The canonical EnvLockr distribution is the Python package:

    pip install "envlockr[keychain]"

Then re-run your command — this npm wrapper will find it automatically.

Docs: https://github.com/RohanRatwani/envlockr-cli
`);
process.exit(1);
