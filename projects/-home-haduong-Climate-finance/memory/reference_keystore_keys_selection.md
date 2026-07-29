---
name: reference_keystore_keys_selection
description: All credentials live once in ~/.config/keys/<provider>.env and are selected per-project by a KEYS= line; ~/.claude/.env holds no secrets
metadata: 
  node_type: memory
  type: reference
  originSessionId: bccc95ab-da2d-4c1a-a8b2-f2eb43af511e
  modified: 2026-07-27T19:04:26.672Z
---

**Single store:** `~/.config/keys/<provider>.env` (mode 0700, ~20 files).
`~/.claude/.env` holds **no secret literal** — only a `KEYS=` line. Rotate in
the keystore; there is no second copy to chase (migrated 2026-07-27).

Selection is `KEYS=` in a project's `.env`. Entry forms: `provider` |
`provider:VAR` | `provider:SRC=DST` (rename on export). Default-deny — an
unlisted provider is not loaded.

**Two mechanisms apply it, because neither alone covers every entry point**
(climate-finance, ticket 0343):

- `~/.claude/scripts/bash-env.sh` — shells with `BASH_ENV` set. The Makefile
  wires it into recipe shells (`SHELL := /bin/bash` + `export BASH_ENV`).
- `scripts/pipeline_keystore.py` — called by `pipeline_loaders` on import, so
  `dvc repro` (which picks its stage shell from `$SHELL` or `/bin/sh`) and a bare
  `uv run python scripts/…` resolve too.

Neither overwrites an already-set variable, so they compose. See
[[feedback_credential_migration_all_entry_points]] for why the shell-only version
was insufficient and how the gap hid.

Identities per context (each renamed to the plain `OPENROUTER_API_KEY` the code reads):

| context | key |
|---|---|
| harness (`~/.claude`) | `OPENROUTER_API_KEY_IDH` |
| climate-finance | `OPENROUTER_API_KEY_CLIMATEFINANCE` |
| aedist | `OPENROUTER_API_KEY_AEDIST` |

**Why:** before this, 8 secrets sat as literals in `~/.claude/.env`, exported
into every process. That is how two keys leaked into test output. It also meant
climate-finance was billing to *aedist's* OpenRouter identity by accident.

**A project `KEYS=` REPLACES the harness one — it does not compose.** bash-env
exports every project-`.env` key verbatim, `KEYS` included, before the provider
block reads `$KEYS`. Measured three ways (0364, 2026-07-27):

| startup directory | harness `KEYS=` survives? |
|---|---|
| no `.env` at all | yes |
| `.env` present, no `KEYS=` line | yes |
| `.env` with a `KEYS=` line | **no — every harness credential drops** |

The trigger is the presence of a `KEYS=` **line**, not of `.env`. So adding one
`KEYS=` line to a `.env` of plain settings silently drops *all* harness
credentials at once — a cliff, invisible until some unrelated tool fails to
authenticate. Harness ticket 0360 tracks compose-vs-override; until it lands, a
project must re-declare every harness credential it still wants.

**How to apply:** never add a credential literal to any `.env` — add it to the
keystore and select it. Consequence of the override: a credential the repo's own
code never imports can still need naming in its `KEYS=`, because anything
launched from that directory inherits the line — which is why climate-finance
selects `hal` for a harness skill. For the harness repo itself `$PWD/.env` *is*
`$HOME/.claude/.env`, so bash-env skips the project parse; its `KEYS=` works
only because the trusted file is sourced first. Related:
[[feedback_bash_env_reinjects_secrets]].

climate-finance `.env` is literal-free (0343) and guarded by
`tests/test_env_has_no_secret_literals.py`, whose `REQUIRED_KEYS_EXPORTS` means
"must resolve for work *started* in this repo", not "is read by code here" —
0364 widened it after the override finding. Its `KEYS=` now selects six,
including `hal:HAL_ID,hal:HAL_PASSWORD` (0364 merged 2026-07-27).
