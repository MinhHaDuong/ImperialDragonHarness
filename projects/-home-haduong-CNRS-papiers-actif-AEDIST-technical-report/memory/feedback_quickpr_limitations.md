---
name: feedback-quickpr-limitations
description: quickpr.sh cannot express renames/deletions and reverts working-tree edits when restoring the starting branch
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 67279a06-6365-498b-a9e8-12f7c9c12264
---

Two quickpr.sh traps hit during the 2026-06-04 raid:

1. **No renames or deletions.** quickpr takes a list of existing files; passing the old path of a `git mv` fails ("file does not exist"). For renames/deletions, do the manual flow: `git switch -c <branch> origin/main`, stage, commit, push, `gh pr create`, `gh pr merge --auto --merge`.
2. **Working tree reverts on return.** quickpr restores the starting branch when done — any working-tree edit to a tracked file that rode into the quickpr branch gets reset to the starting branch's committed state in your worktree. The content is safe on the PR branch, but your local copy silently reverts; re-fetch from origin (or re-apply) if you need to keep working on it.

**How to apply:** use quickpr only for additive file-list chores (new tickets, doc tweaks committed in place); anything involving git mv, rm, or files you keep editing afterwards → manual branch + PR.
