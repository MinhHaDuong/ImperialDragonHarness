---
name: feedback_worktree_search
description: When checking worktrees, search parent directories and /tmp for stale worktree-like directories, not just git worktree list
type: feedback
---

When asked about worktrees, don't rely solely on `git worktree list`. Also scan likely locations for leftover worktree directories (e.g., sibling dirs in the parent folder, /tmp, home directory). The user runs parallel sessions and worktrees may not always be properly cleaned up.

**Why:** `git worktree list` only shows worktrees git knows about. Orphaned directories from improperly removed worktrees won't appear there but still consume disk and cause confusion.

**How to apply:** When checking repo status, always `ls` the parent directory and `/tmp` for directories that look like worktree copies of the repo (similar names, containing `.git` files).
