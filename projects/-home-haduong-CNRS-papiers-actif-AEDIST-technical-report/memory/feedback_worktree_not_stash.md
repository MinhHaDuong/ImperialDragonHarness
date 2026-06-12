---
name: Use worktrees, never stash-and-checkout
description: When editing a different branch, use git worktree instead of stash+checkout to avoid cross-branch contamination
type: feedback
---

Use `git worktree add` for cross-branch work, never `git stash` + `git checkout`.

**Why:** Stash pop on the wrong branch leaked 80 files of main-tip changes onto frontier-bench, causing confusion and requiring manual cleanup. Stash is branch-unaware and mixes working tree state across branches.

**How to apply:** When a task requires committing to a branch other than the current one, create a temporary worktree (`git worktree add /tmp/<branch> <branch>`), do the work there, push, then `git worktree remove`. Or use the Agent tool with `isolation: "worktree"`.
