---
name: parallel-push-during-investigation
description: User pushes directly to main while agent investigates; branch must come from origin/main not local HEAD to avoid stale-base conflicts
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1224353e-6a60-488c-9d0f-a9ce45f93f09
---

Always branch from `origin/main` (after `git fetch origin`), never from local HEAD, when the user may be pushing directly in parallel.

**Why:** 2026-05-26 — while investigating slide state, the user pushed 4 commits to origin/main. Local main was stale. Branching from `origin/main` after fetch let us land cleanly on top of their work without conflicts. Branching from local HEAD would have produced a PR missing 4 commits and triggered a rebase conflict.

**How to apply:** First action after `EnterWorktree` when working near slides/manuscript: `git fetch origin`, then `git switch -c <branch> origin/main`. Never use local HEAD as base without checking `git log HEAD..origin/main` first (new workflow.md §2 codifies this).
