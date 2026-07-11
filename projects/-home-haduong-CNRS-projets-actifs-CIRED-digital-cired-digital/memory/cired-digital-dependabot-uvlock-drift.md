---
name: cired-digital-dependabot-uvlock-drift
description: cired.digital Dependabot floor bumps drift uv.lock — check locked-vs-floor before merging
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d9e36fb-8b06-47db-869d-f03d3d5477f5
---

In `CIRED/cired.digital`, Dependabot PRs bump only `pyproject.toml` lower bounds and never touch `uv.lock`. CI (`.github/workflows/CI.yml`) installs with plain `uv sync --group dev` — no `--locked` — so a floor raised ABOVE the locked version still passes green while leaving `uv.lock` inconsistent on `main`.

**Why:** plain `uv sync` re-resolves in the runner; the committed lockfile is never validated. Green CI does not mean the lockfile is consistent.

**How to apply:** Before merging a Dependabot floor bump, compare the new floor against the locked version (`grep -A1 'name = "<pkg>"' uv.lock`). If the floor exceeds the lock, regenerate: consolidate the bumps on one branch, run `uv lock`, verify `uv lock --locked` exits 0, then merge. On 2026-06-23 PRs #261/#263/#264 (plotly, ibis-framework, pyarrow) all had floor > lock; consolidated into #271 with a synced lockfile, closed the originals as superseded.

Standing fix not yet applied: add `uv lock --locked` to CI and/or configure Dependabot to manage `uv.lock`. Related: [[cired-digital-merge-and-tracker]]
