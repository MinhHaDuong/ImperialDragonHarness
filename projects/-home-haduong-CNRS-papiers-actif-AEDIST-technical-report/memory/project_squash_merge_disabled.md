---
name: project-squash-merge-disabled
description: Squash merge is disabled on aedist-technical-report as of 2026-05-25; use --merge everywhere
metadata: 
  node_type: memory
  type: project
  originSessionId: 99c67ddd-8a00-4c3d-b516-43ff27adea3a
---

Squash merge was disabled on 2026-05-25. The repo now uses regular merge commits only.

**Why:** User decision. Confirmed when `gh pr merge 522 --squash --auto` failed with "Merge method squash merging is not allowed on this repository."

**How to apply:**
- All `gh pr merge` calls: use `--merge` not `--squash`
- All `gh api .../merge` calls: use `merge_method=merge` not `merge_method=squash`
- Auto-merge flow: `gh pr merge <N> --merge --auto` (no `--delete-branch` in worktrees)
- `git merge-base --is-ancestor` now works correctly for new PRs
- For branches predating 2026-05-25: the PR-number grep probe in healthcheck still handles old squash-merged history correctly
