---
name: BASH_ENV secret loading pattern
description: How harness loads .env secrets into bash subprocesses without leaking to ps -ef
type: project
originSessionId: 2021dbc7-bda1-4b1a-995a-8f6901ec1ce2
---
Secrets are loaded into Claude Code bash subprocesses via `BASH_ENV`, not `CLAUDE_ENV_FILE`.

**Why:** `CLAUDE_ENV_FILE` causes Claude Code to inline `KEY=VALUE` pairs as shell assignments before each Bash tool call (visible in `ps -ef` to all local users). Discovered 2026-05-03 when orphaned processes from April 30 were found exposing all API keys.

**How to apply:** 
- `settings.json` → `env.BASH_ENV` → `scripts/bash-env.sh`
- `bash-env.sh` uses `set -a` / `set +a` to source `~/.claude/.env` and `$PWD/.env`
- `bash-env.sh` must NOT have `set -euo pipefail` (it's sourced, not executed — flags would propagate into calling shell)
- `bash-env.sh` is excluded from the `pipefail-guard` CI check alongside `shell-init.sh`
- Never write secrets back to `CLAUDE_ENV_FILE` in hooks
