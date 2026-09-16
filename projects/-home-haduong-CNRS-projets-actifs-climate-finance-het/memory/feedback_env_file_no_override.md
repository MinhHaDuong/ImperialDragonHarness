---
name: env-file-no-override
description: uv --env-file does NOT override already-set ambient env vars — stale shell exports shadow refreshed .env keys
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5d889db-150a-4c5a-829a-2678315e0e35
  modified: 2026-07-24T20:22:19.033Z
---

`uv run --env-file .env` leaves any variable already present in the ambient
environment untouched.

**Why:** 2026-07-24, a refreshed OpenRouter key kept 401-ing because the
session shell had inherited the old key; the .env value never applied.

**How to apply:** after rotating a credential, pass it explicitly for the
invocation (`VAR=$(grep '^VAR' .env | cut -d= -f2) uv run ...`) or start a
fresh shell. Secrets live in the harness env, not the project .env
([[project ticket 0316]]); Quarto/hand-numbered crossref and population
checks aside, always suspect ambient shadowing when a rotated key
"doesn't work".
