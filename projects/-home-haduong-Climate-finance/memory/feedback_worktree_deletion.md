---
name: Never force-delete a worktree without checking active sessions
description: Force-removing a worktree that another Claude session is using destroys its working directory
type: feedback
originSessionId: b0ad69a4-551a-4c51-ad1d-3c2e0e738f34
---
Never run `git worktree remove --force` on a worktree during an end-session hygiene sweep without first confirming no other Claude session is actively using it.

**Why:** During the 2026-04-25 end-session, I force-deleted `orchestrator-112-115` while another Claude session was mid-execution there. The directory vanished, breaking the other session's working context and losing any uncommitted state.

**How to apply:** Before removing any worktree that is NOT locked:
1. Check if there's another open terminal/session that might be using it.
2. If uncertain, skip it — stale worktrees are harmless, deleted active worktrees are not.
3. Reserve `--force` for worktrees whose session has clearly exited (e.g., the branch was merged and no PID holds the directory).

The `locked` status only protects against git's own cleanup, not manual `--force` removal. Unlocked ≠ abandoned.
