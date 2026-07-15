---
name: feedback-memory-writes-bypass-worktree-gate
description: Memory-file writes to the primary checkout are blocked by the live tool guard during a worktree session — write the worktree copy and land it via the branch's own PR
metadata:
  type: feedback
---

An earlier version of this note claimed `~/.claude/projects/*/memory/**`
writes bypass worktree isolation by design, citing an exemption in
`scripts/pretooluse-worktree-path-guard.sh`. Observed behavior on
2026-07-15 contradicts that: a `Write` to the primary-checkout memory path
was blocked with "Edit the worktree copy of this file instead of the
shared-checkout path" — a different message than that script emits, meaning
a platform-level Write/Edit gate now enforces worktree isolation on this
path independent of the custom hook's exemption.

**Why:** trust the live guard's exit behavior over a stored claim about it
([[feedback_memory_writes_bypass_worktree_gate]] itself, ironically) — the
hook script's carve-out may be dead code now, or the platform added its own
stricter check on top. Either way, the write was in fact blocked.

**How to apply:** during a worktree session, write memory files to the
worktree-rooted path (`<worktree>/projects/*/memory/**`), commit them, and
land them through that branch's normal PR — do not assume a bare
primary-checkout write will succeed. If a future session confirms the
exemption works again (no block), update this note rather than trusting
either version blindly.
