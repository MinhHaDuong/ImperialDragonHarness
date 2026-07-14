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

**Provider secrets load least-privilege via `KEYS=`** (#588/#593): the project `.env` opts in with `KEYS=entry,entry`; only those validated (`^[a-z0-9-]+$`) providers' user-owned `~/.config/keys/<name>.env` are read. Default-deny (no `KEYS` line → no provider secrets); name validation blocks path traversal out of `~/.config/keys/`. This is cooperative scoping (shrinks default exposure), NOT access control against a hostile `.env`.

**Three `KEYS=` entry forms (ticket 0337):** each comma-separated entry is one of —
- `provider` — source the WHOLE `~/.config/keys/<provider>.env` (all its vars enter the env). Unchanged.
- `provider:VAR` — export ONLY `VAR` from that file, under name `VAR`.
- `provider:SRC=DST` — export ONLY `SRC`, renamed to `DST`. No sibling var enters the env.

Selection is EXPLICIT/VERBOSE — no suffix-stripping convention. `SRC`/`DST` each validated `^[A-Za-z_][A-Za-z0-9_]*$`; a malformed entry warns `ignoring invalid KEYS entry: <entry>` and skips (default-deny); a named `SRC` absent from the file warns `KEYS var not found: <provider>:<SRC>` and skips. **Mechanism (least-privilege at the export boundary, not the filesystem — one file per provider, no proliferation):** a `provider:...` entry does NOT source the file into the live env; it sources it in an ISOLATED `bash -c` subshell, extracts only `SRC` via indirect expansion, and the parent does `export "$DST=$val"` with the value assigned LITERALLY (command-sub captures the string, never `eval`'d) — so a value with spaces/`$(...)` is verbatim, and `SRC`'s siblings (KIEU, EXPIRED_*) die with the subshell. The `if val="$(...)"` wrapper keeps the sub's exit status from tripping `set -e`. Bare `provider` keeps the whole-file `set -a; source` path. Test: `tests/test_bash_env_keys_selection_explicit.sh`.

**Robustness (ticket 0335):** strict parse tolerates CRLF (trailing `\r` dropped), is bounded by a 256 KiB byte cap (oversized project `.env` skipped whole with a stderr warning), and the realpath dedup uses `|| true` so an absent file cannot abort the script under an active `set -e` in the sourcing shell.

**How to apply:**
- `settings.json` → `env.BASH_ENV` → `scripts/bash-env.sh`
- `bash-env.sh` must NOT have `set -euo pipefail` (it's sourced, not executed — flags would propagate into the calling shell); excluded from the `pipefail-guard` CI check alongside `shell-init.sh`.
- Never write secrets back to `CLAUDE_ENV_FILE` in hooks.
- Tests: `tests/test_bash_env_project_env_parse.sh`, `tests/test_bash_env_keys_selection.sh`, `tests/test_bash_env_robustness.sh` (auto-run by `tests/test_bash_suites.py`).
