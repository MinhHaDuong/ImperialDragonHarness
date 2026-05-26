---
name: api-keys-in-claude-env
description: API keys split between ~/.claude/.env (user-level) and project .env; use UV_ENV_FILE=.env for experiment scripts
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4ce9fb20-3b79-41a4-90ba-e2b94004e133
---

API keys are split across two locations:

**User-level** `~/.claude/.env`: Anthropic, Zotero, and other personal keys. Loaded by the on-start hook via `UV_ENV_FILE`.

**Project-level** `/home/haduong/aedist-technical-report/.env`: OPENROUTER_API_KEY (and likely Tavily, Mistral, OpenAI). This is what experiment scripts need.

For running experiment scripts (e.g. `exp2_interactive_smoke.py`):
```bash
UV_ENV_FILE=.env PYTHONPATH=. uv run python experiments/sota/...
```

Not `UV_ENV_FILE=~/.claude/.env` — that misses OPENROUTER_API_KEY and causes the dialogue classifier to default to `no_report` on every turn, burning extra API budget.
