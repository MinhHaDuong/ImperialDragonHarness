---
name: feedback_worktree_isolation
description: Every conversation must run in its own worktree via EnterWorktree — parallel VSCode conversations share cwd otherwise
type: feedback
---

Every conversation runs in its own throwaway worktree via `EnterWorktree`. Branches hold durable state, worktrees are ephemeral.

**Why:** Parallel VSCode conversations share the same working directory. Branch switches in one conversation silently corrupt another — the "random teleport" bug.

**How to apply:** Session-start step 3 calls `EnterWorktree` with a descriptive name before any work. `.worktreeinclude` auto-copies `.env` and `.dvc/config.local`. Works in VSCode/Desktop; CLI does not support `.worktreeinclude` yet.
