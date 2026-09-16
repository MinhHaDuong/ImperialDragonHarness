---
name: verify-simplify-isolation
description: /verify simplify step writes directly to the PR branch; changes leak into working tree and origin
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 60765da7-1ecb-410a-9fa2-44e30fdc3bc9
---

The `/verify` skill's simplify step lacks proper worktree isolation. When it runs, it:
- Pushes fix commits directly to the feature branch (not a detached/temp branch)
- Sometimes spawns sibling branches (e.g. t0142) as side-effects
- Leaves the local working tree in a diverged state relative to origin

**Why:** The simplify agent operates on the checked-out branch instead of an isolated copy; its commits go straight to origin.

**How to apply:** After `/verify` completes, always do `git fetch origin && git log origin/<branch>` before assuming the branch is in the state you left it. If /verify pushed extra commits, reconcile before doing further work (rebase, cherry-pick, or accept). When rebasing a sibling branch onto master after squash-merge, use cherry-pick of the unique commits rather than `git rebase` — the squash merge breaks ancestry and rebase re-applies already-merged work.

[[squash-merge-sync]]
[[celebrate-squash-precheck]]
