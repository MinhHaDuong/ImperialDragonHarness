---
name: feedback-worktree-stale-after-agent
description: "After an isolation:worktree agent pushes, the parent worktree's working tree has phantom old-name files — exit and re-enter instead of manual cleanup"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d376c398-65f4-4a0d-8b7f-0ed9717b3dbd
---

When an `Agent(isolation: "worktree")` renames files and pushes to a shared branch, the parent worktree retains the old-name files on disk. `git checkout -- .` restores tracked content but doesn't clean up untracked old names; `git clean` is guarded.

**Why:** The agent works in its own worktree copy; `git mv` renames happen there, not in the parent. The parent's working tree becomes stale relative to the branch HEAD it shares.

**How to apply:** After a worktree-isolated agent finishes a rename-heavy operation, don't try to sync the parent worktree manually. Either (a) verify via `git show`/`git grep` on the committed tree, or (b) exit the worktree and re-enter to get a fresh checkout.
