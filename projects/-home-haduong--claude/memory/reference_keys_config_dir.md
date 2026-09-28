---
name: reference-keys-config-dir
description: "API keys live in ~/.config/keys/ — one .env file per provider; source the file, never inline the value. Provider inventory is tier-2 data in the private overlay."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 280e20e3-95c7-41c7-ae2-2e5aedbe8beb
---

The author's API credentials live in `~/.config/keys/`, one `.env` file per
provider (the full provider inventory, and which non-.env credential files
live there, is tier-2 data in `~/.config/harness/private/keys.md`).

When a task needs a provider key (e.g. for reviewer seats), source the matching
file — never inline the value into argv or chat text. Loading into Claude Code
bash subprocesses goes through the [[BASH_ENV secret loading pattern]]
(`BASH_ENV` → `bash-env.sh`), not `CLAUDE_ENV_FILE`. Verify presence only
with `[ -n "${VAR:-}" ]`; never echo.

## The keystore is not the only copy (measured 2026-09-16)

`~/.claude/.env` asserts "Rotate in the keystore only — there is no second copy
of any key". Measured 2026-09-16, the keystore alone would have missed all three:

- **A neighbouring runtime keeps its own store.** A CLI's own auth file (mode
  600) holds its own API key beside an OAuth token set and a `last_refresh`
  stamp. That runtime authenticates by a login flow that writes a file, not by
  a helper invoked at need — so rotating the provider key in the keystore
  leaves it on the old value until it is re-logged.
- **Timestamped backups.** A keystore backup file held the previous value of a
  provider key; deleted 2026-09-16 after confirming it defined no variable
  absent from the current file. Compare NAMES before deleting such a backup —
  never assume the newer file is a superset.
- **Expired keys kept in place.** A provider file carries several
  `EXPIRED_..._API_KEY_*` entries. Whether each is genuinely revoked cannot be
  checked from inside a session.

The keystore also provisions identities ahead of adapters — a credential in the
keystore is not evidence that a runtime is wired up. Related:
[[project_bash_env_secret_loading]].
