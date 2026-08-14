---
name: feedback-ergprmerge-stale-worktree-after-api-push
description: "erg-pr-merge bounces non-fast-forward when gaze pushed fixes via GitHub API and the executor worktree is stale; recover by detached cherry-pick, never rerun"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f10ac93f-e26c-4c6e-91eb-08c84ce03ec3
  modified: 2026-08-12T08:58:54.859Z
---

New trigger for the known merge-bounce class (2026-08-12, PR #87): a /gaze
run that commits fixes through the GitHub Contents API (because worktree
guards blocked local git) advances the remote branch while the Execute
agent's local worktree stays behind. `erg-pr-merge -C <executor-worktree>`
then commits the ticket-close on the stale tip and its push is rejected
non-fast-forward.

**Why:** erg-pr-merge is not idempotent past the close step; rerunning it
fails `close: no ticket found` and hand-merging loses the close commit.

**How to apply:** worktrees share one object database, so recover from the
session worktree: `git fetch`, `git checkout --detach origin/<branch>`,
`git cherry-pick <close-commit-sha>` (printed by the failed run),
`git push origin HEAD:<branch>` (fast-forward), then `gh pr merge N --merge`
directly. A "Pull Request is not mergeable" right after the push is GitHub's
transient recompute — wait a few seconds and retry once. Prevention: before
calling erg-pr-merge on an executor worktree, check the branch tip matches
origin (gaze reports when it pushed commits).
