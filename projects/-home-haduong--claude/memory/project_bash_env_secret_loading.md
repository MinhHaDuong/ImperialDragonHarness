---
name: BASH_ENV secret loading pattern
description: How harness loads .env secrets into bash subprocesses without leaking to ps -ef
type: project
originSessionId: 2021dbc7-bda1-4b1a-995a-8f6901ec1ce2
---
Secrets are loaded into Claude Code bash subprocesses via `BASH_ENV`, not `CLAUDE_ENV_FILE`.

**Why:** `CLAUDE_ENV_FILE` causes Claude Code to inline `KEY=VALUE` pairs as shell assignments before each Bash tool call (visible in `ps -ef` to all local users). Discovered 2026-05-03 when orphaned processes from April 30 were found exposing all API keys.

**Two .env sources, DIFFERENT trust** (`scripts/bash-env.sh`, sourced on every subprocess):
- `~/.claude/.env` — user-owned, TRUSTED: **sourced** as shell code (full expansion), inside `set -a`/`set +a`.
- `$PWD/.env` — project-level, UNTRUSTED (an agent/clone/project write can place it): **strict-parsed** `KEY=VALUE`, never sourced. Values assigned LITERALLY (no eval/`$()`/backticks), one surrounding quote-pair stripped, non-identifier keys skipped. Any guard-namespaced key (substring `GUARD_`, covering `GUARD_*` and the `_GUARD_*` override pair) is REFUSED, so it cannot forge a per-process guard nonce or the worktree-path override.

**Provider secrets load least-privilege via `KEYS=`** (#588/#593): the project `.env` opts in with `KEYS=name,name`; only those validated (`^[a-z0-9-]+$`) providers' user-owned `~/.config/keys/<name>.env` are sourced. Default-deny (no `KEYS` line → no provider secrets); name validation blocks path traversal out of `~/.config/keys/`. This is cooperative scoping (shrinks default exposure), NOT access control against a hostile `.env`.

**Robustness (ticket 0335):** strict parse tolerates CRLF (trailing `\r` dropped), is bounded by a 256 KiB byte cap (oversized project `.env` skipped whole with a stderr warning), and the realpath dedup uses `|| true` so an absent file cannot abort the script under an active `set -e` in the sourcing shell.

**How to apply:**
- `settings.json` → `env.BASH_ENV` → `scripts/bash-env.sh`
- `bash-env.sh` must NOT have `set -euo pipefail` (it's sourced, not executed — flags would propagate into the calling shell); excluded from the `pipefail-guard` CI check alongside `shell-init.sh`.
- Never write secrets back to `CLAUDE_ENV_FILE` in hooks.
- Tests: `tests/test_bash_env_project_env_parse.sh`, `tests/test_bash_env_keys_selection.sh`, `tests/test_bash_env_robustness.sh` (auto-run by `tests/test_bash_suites.py`).
