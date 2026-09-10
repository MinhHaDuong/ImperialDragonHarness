---
name: feedback_background_session_isolation_blocks_primary_writes
description: "A background session cannot write the shared checkout even outside a worktree — a second guard refuses on isolation, not on path, so leaving a worktree does not unblock a memory write"
metadata:
  type: feedback
---

Two different guards refuse a primary-checkout write, in two different contexts,
with two different messages. Confusing them makes a documented remedy fail.

- **Inside a worktree session**: "Edit the worktree copy of this file instead of
  the shared-checkout path" — the path guard, recorded in
  [[feedback_memory_writes_bypass_worktree_gate]]. Remedy: write the worktree
  copy, land it via the branch's PR.
- **In a BACKGROUND session, outside any worktree**: "This background session
  hasn't isolated its changes yet. Call EnterWorktree first" — a separate
  isolation guard that keys on the *session kind*, not on the path. Observed
  first-hand 2026-09-10, on a `Write` to
  `projects/-home-haduong--claude/memory/` from the primary checkout after a
  clean `ExitWorktree`.

**Why:** the second guard has no memory exemption and no worktree to be outside
of, so the usual escape does not apply. `/roar` step 6 told sessions to defer
the memory write until after leaving the worktree — correct for an interactive
session, and in a background session it lands exactly on this refusal. Following
it reproduced the silent loss it exists to prevent: the denial reads as "memory
is unavailable in this context", the lesson goes into the final message, and
after the worktree is gone nothing distinguishes it from a session that had
none. Fixed in roar on 2026-09-10 (PR #860).

**How to apply:** read *which* refusal you got. Isolation refusal means create a
fresh worktree, write there, and land a memory-only PR — do not retry in the
primary checkout and do not conclude memory is unavailable. Path refusal means
you are in a worktree and should write its copy. A `grep` of `scripts/` and
`settings*.json` finds neither message: both are platform-native, so the repo
holds no trace of them and this note is the record. Related:
[[feedback_worktree_path_trap_needs_guard]].
