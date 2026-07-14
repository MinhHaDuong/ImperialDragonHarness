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
