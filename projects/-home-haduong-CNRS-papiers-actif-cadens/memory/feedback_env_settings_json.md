---
name: Machine-specific env vars belong in .env, not settings.json
description: .claude/settings.json env overrides are committed and machine-specific values cause silent failures on other machines
type: feedback
originSessionId: ed60f2cf-e8df-4506-b5b1-c1750f1fd999
---
Never put machine-specific env vars (paths, credentials) in `.claude/settings.json` — it's committed to git and silently overrides `.bashrc` on every machine. Use a gitignored `.env` file instead, loaded via `uv run --env-file .env` in the Makefile.

**Why:** `CADENS_RAW_DIR=/data/projets/cadens/raw` (padme's path) was committed in `settings.json`, causing `load_raw_df()` to silently return an empty DataFrame on doudou. Cost a full debugging round-trip.

**How to apply:** When an env var is machine-specific, put it in `.env` (gitignored), add `.env.example` with a placeholder, and wire `Makefile` targets with `$(if $(wildcard .env),--env-file .env,)`.
