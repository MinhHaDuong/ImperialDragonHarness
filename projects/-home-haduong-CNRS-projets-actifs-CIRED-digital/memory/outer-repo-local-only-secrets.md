---
name: outer-repo-local-only-secrets
description: "Outer CIRED.digital repo is local-only (no git remote); secrets/ is gitignored, managed via push_secrets not git"
metadata: 
  node_type: memory
  type: project
  originSessionId: d85d05f6-f79f-4dc3-923c-6868021a8cf6
---

The outer repo at `/home/haduong/CNRS/projets/actifs/CIRED.digital` (branch `master`) has **no git remote** — it is a local-only working repo. The inner app repo `cired.digital/` is the one with a forge (`git@github.com:CIRED/cired.digital.git`, branch `main`).

Consequences:
- The outer repo's branch-and-PR gate does **not** apply (nowhere to open a PR). Commits there land directly on `master`. The usual "master is read-only, everything via PR" rule presupposes a forge this repo lacks.
- `cired.digital/` is tracked in the outer repo as a **bare gitlink** (mode 160000), not a registered submodule — there is no `.gitmodules`, so `git submodule` commands fail. The recorded gitlink SHA drifts from the inner repo's `main` and has no external consumer, so bumping it is low-stakes local bookkeeping — fold it into a normal commit rather than ceremonialising it.

**Why:** On 2026-06-23 the outer repo was found tracking `secrets/env/*.env` and `secrets/hosting/*` (live API keys + DB passwords) with no `.gitignore` rule. Purged from all history with git-filter-repo and `secrets/` added to `.gitignore`. Exposure had been local-disk only (no remote ever).

**How to apply:** `secrets/` lives on disk and on the VPS, synced via `cired.digital/deploy/ops/push_secrets.sh` (rsync) — never via git. Never re-track it. Edit secret files in `CIRED.digital/secrets/env/` then `push_secrets.sh`; a key swap also needs the r2r container **recreated**, not restarted — see [[r2r-embeddings-openai-billing]].
