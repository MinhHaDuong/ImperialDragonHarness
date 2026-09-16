---
name: reference-keys-config-dir
description: "API keys live in ~/.config/keys/ — one .env file per provider (openrouter.env, anthropic.env, openai.env, mistral.env, github.env, zotero.env, ...)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 280b20e3-95c7-41c7-ae4a-2e5aedbe8beb
---

The author's API credentials live in `~/.config/keys/`, one `.env` file per
provider: `openrouter.env`, `anthropic.env`, `openai.env`, `deepseek.env`,
`mistral.env`, `github.env`, `huggingface.env`, `zotero.env`,
`zotero-archive-cired.env`, `hal.env`, `istex.env`, `janus.env`,
`openalex.env`, `semanticscholar.env`, `tavily.env`, `zenodo.env`, plus
`netrc` and `eduroam.ids` (stated by the author 2026-07-14).

When a task needs a provider key (e.g. `OPENROUTER_API_KEY` for reviewer
seats), source the matching file — never inline the value into argv or chat
text. Loading into Claude Code bash subprocesses goes through the
[[BASH_ENV secret loading pattern]] (`BASH_ENV` → `bash-env.sh`), not
`CLAUDE_ENV_FILE`. Verify presence only with `[ -n "${VAR:-}" ]`; never echo.

## The keystore is not the only copy (measured 2026-09-16)

`~/.claude/.env` asserts "Rotate in the keystore only — there is no second copy
to chase." That was false on padme in three ways, and a rotation scoped to the
keystore alone would have missed all three:

- **A neighbouring runtime keeps its own store.** `~/.codex/auth.json` (mode
  600) holds its own `OPENAI_API_KEY` beside an OAuth token set and a
  `last_refresh` stamp. Codex authenticates by a login flow that writes a file,
  not by a helper invoked at need — so rotating `openai` in the keystore leaves
  Codex on the old value until it is re-logged.
- **Timestamped backups.** `openrouter.env.bak-20260916T113037` held the
  previous value; deleted 2026-09-16 after confirming it defined no variable
  absent from the current file. Compare NAMES before deleting such a backup —
  never assume the newer file is a superset.
- **Expired keys kept in place.** `openrouter.env` carries five
  `EXPIRED_OPENROUTER_API_KEY_*` entries (CIRED_DIGITAL, CLAUDE, IDH, KIEU,
  KILOCODE). Whether each is genuinely revoked cannot be checked from inside a
  session.

The keystore also provisions an `OPENROUTER_API_KEY_PI` identity although
`adapters/` contains only `claude-code/` — the credential exists before the
adapter does, so an identity in the keystore is not evidence that a runtime is
wired up. Related: [[project_bash_env_secret_loading]].
