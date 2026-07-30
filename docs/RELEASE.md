# Release process

Steps to cut a new EnvLockr release. Example below is for **2.0.0**.

## 0. Pre-flight

- [ ] `python run_tests.py` passes locally
- [ ] CI green on the release PR
- [ ] `__version__` in `envlockr.py` and `version` in `pyproject.toml` match the tag
- [ ] `CHANGELOG.md` has an entry for this version
- [ ] `demo.gif` generated and referenced in README (see `DEMO.md`) — optional but recommended

## 1. Merge the release PR

```bash
gh pr merge <PR#> --squash --delete-branch
git checkout main && git pull
```

## 2. Tag

```bash
git tag -a v2.0.0 -m "EnvLockr v2.0.0"
git push origin v2.0.0
```

## 3. Build

```bash
python -m pip install --upgrade build twine
rm -rf dist/ build/ *.egg-info
python -m build                 # creates dist/*.whl and dist/*.tar.gz
twine check dist/*              # must pass before upload
```

## 4. Publish to PyPI

You need a PyPI API token (https://pypi.org/manage/account/token/). Either set
`TWINE_USERNAME=__token__` / `TWINE_PASSWORD=<token>`, or use a `~/.pypirc`.

```bash
# (optional) test on TestPyPI first:
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps envlockr==2.0.0

# real upload:
twine upload dist/*
```

Verify:

```bash
pip install --upgrade "envlockr[keychain]"
envlockr --version            # → EnvLockr v2.0.0
```

> 💡 Consider configuring PyPI **Trusted Publishing** (OIDC) so a GitHub Actions
> release workflow can publish without a long-lived token.

## 5. GitHub Release

```bash
gh release create v2.0.0 --title "EnvLockr v2.0.0" --notes-file - <<'NOTES'
## 🔐 v2.0.0 — keychain keys, `run`, `verify`, hardening

### Highlights
- **OS keychain master key** (`pip install "envlockr[keychain]"`) — the key no
  longer sits in a plaintext file next to the vault. `secure-key` migrates
  existing installs.
- **`envlockr run -- <cmd>`** — inject secrets into a subprocess; no `.env` on disk.
- **`envlockr verify`** — check whether stored keys are still live (Stripe,
  OpenAI, GitHub, Slack).
- **Profiles** via `--env` / `ENVLOCKR_ENV`.
- **`--value`/`--stdin`** for non-interactive `add`/`update` (CI-friendly).

### Security
- `encrypt-vault`: random per-file salt + PBKDF2 600k iterations (v1 files still
  decrypt). Fixed Windows UTF-8 console crash.

### Tooling
- gitleaks-aware secret-scan action; cross-platform test CI (3.8–3.12); tests
  now shipped in-repo.

Full changelog: https://github.com/RohanRatwani/envlockr-cli/blob/main/CHANGELOG.md
NOTES
```

## 6. Post-release

- [ ] Announce (see `personal/LAUNCH_POSTS.md`)
- [ ] Enable GitHub Discussions + Issues, add repo topics: `secrets`,
      `environment-variables`, `security`, `cli`, `python`, `dotenv`
- [ ] Watch issues/PRs for the first 48h
