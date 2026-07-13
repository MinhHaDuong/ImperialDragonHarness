---
name: supervisor-checkpoint-pattern
description: The primary supervisor chat orchestrates, never executes; clean checkpoint = watch for worker quiescence, then merge leftover ready PRs, leave drafts to their owners
metadata:
  type: feedback
---

Author doctrine (2026-07-13, supervisor chat): "You don't execute nothing, you
are the orchestrator." The primary supervisor chat surveys, dispatches to
worker instances, and verifies — it does not pick up tickets itself.

**Why:** Worker sessions run in parallel and own their branches; a supervisor
that executes competes with its own workers for worktrees and branches (the
shared-worktree contention class, [[shared-worktree-live-session-contention]]).

**How to apply:** For a clean checkpoint: (1) arm a monitor on the open-PR set
plus a remote-heads hash, quiescence = empty PR queue or 30 min without
change; (2) then tidy — merge the ready CI-green PRs the workers left behind
(union-merge origin/main into a branch on memory-index conflicts), leave
draft PRs to their owners, prune merged branches and stale worktrees, sync
main by ref. Merging leftover ready PRs and routine hygiene are supervisor
work; finishing a draft is not — it belongs to the owning session unless the
author reassigns it (as with PR #522).
