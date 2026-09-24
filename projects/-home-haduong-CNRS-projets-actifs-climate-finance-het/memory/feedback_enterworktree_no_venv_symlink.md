---
name: feedback_enterworktree_no_venv_symlink
description: "EnterWorktree and agent isolation worktrees do not run the post-checkout hook, so .venv is absent and a bare uv run builds a stray 129-package venv; symlink /data/envs/venv/oeconomia first, copy .env, symlink data/jetp/documents from the primary"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a12625da-f40d-43cd-8b7d-fd6f422a6920
  modified: 2026-09-22T06:34:44.257Z
---

Seen 2026-09-21: in the session worktree, `uv run python …` printed "Creating
virtual environment at: .venv" and installed 129 packages, because
`.githooks/post-checkout` (which symlinks `.venv` and `.dvc/cache` and stages
JETP documents) had not run. The primary's `core.hooksPath` pointed at a
missing `hooks/` directory that night, so no hook ran anywhere.

**Why:** worktrees created by EnterWorktree or `Agent(isolation: worktree)`
get `.worktreeinclude` copies at best; the shared env, the DVC documents and
the VNM release pointer are not there.

**How to apply:** before any `make` or `uv run` in a fresh worktree:
`ln -s /data/envs/venv/oeconomia .venv`; copy `.env` from the primary if
absent (no secret in it); `ln -s <primary>/data/jetp/documents data/jetp/documents`
and the same for `data/jetp/releases/vnm-migration-0764.json` when the
observatory build or the browser recipe needs them; use `uv run --no-sync`.
Put these lines in every delegated agent's brief. A stray `.venv` directory
is moved aside, not `rm -rf`'d (the destructive-bash guard blocks that).
Related: [[feedback_worktree_guard_usr_bin_git]], [[project_worktree_env_data]].
