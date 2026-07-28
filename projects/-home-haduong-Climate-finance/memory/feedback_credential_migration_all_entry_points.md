---
name: feedback_credential_migration_all_entry_points
description: "Moving credentials out of .env breaks every entry point that fed them via `uv run --env-file`; verify make, direct script, and dvc separately"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d8b8fbb-6baa-4f83-8431-b9c37c1398d2
  modified: 2026-07-27T14:21:40.907Z
---

Migrating a credential out of `.env` into the keystore (ticket 0343) silently
broke three entry points, found one at a time, each only after fixing the last:

- `make …` — the Makefile fed secrets via `uv run --env-file .env`, and
  `~/.bashrc` does not load the harness bash loader, so a plain terminal got
  *nothing*. Fixed by `export BASH_ENV := $(wildcard …)` plus `SHELL := /bin/bash`
  (BASH_ENV is honoured only by non-interactive bash).
- `bash scripts/run_corpus_pipeline.sh` — its own documented invocation has no
  `BASH_ENV`. Fixed by sourcing the loader in the script, after the `cd`.
- `dvc repro` — DVC picks its stage shell from `$SHELL` or `/bin/sh`, and make's
  `SHELL` is make-internal and unexported, so neither earlier fix reached it.
  Fixed generally by `scripts/pipeline_keystore.py`, applied at the
  `pipeline_loaders` import every script already performs.

**Why:** the agent's own Bash tool always has `BASH_ENV` set, so every check run
from here passes while the author's terminal is broken. Verifying on the agent
path proves nothing about the paths a human uses. And the failure is silent: a
missing API key reads as "use the free tier", so an unauthenticated multi-hour
harvest looks like it is working.

**How to apply:** when a credential changes *source* (not value), enumerate the
entry points before declaring done — `make`, a bare `uv run python scripts/…`,
`dvc repro`, and any standalone `bash scripts/*.sh` — and test each in a
hermetic `env -i` shell with no ambient `BASH_ENV`. Prefer one resolver at a
shared import choke point over N shell-level fixes; shell wiring leaves a next
entry point open every time. Related: [[reference_keystore_keys_selection]],
[[feedback_env_file_no_override]].

Side effect worth knowing: wiring `BASH_ENV` into recipes makes the loader
re-apply `.env` per recipe shell, so `VAR=x make target` is silently ignored for
any variable `.env` defines. Command-line overrides still work on a leaf process.
