---
name: feedback-memory-writes-bypass-worktree-gate
description: "Memory-file writes to the primary checkout are blocked by the live tool guard during a worktree session — write the worktree copy and land it via the branch's own PR"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bb7d1a1f-202d-45bc-94f6-3ab7979c2dd9
  modified: 2026-07-24T20:23:14.554Z
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

**Scope narrowed 2026-07-24:** the block is specific to *worktree* sessions.
A session that never called `EnterWorktree` wrote
`projects/-home-haduong--claude/memory/*.md` directly in the primary
checkout with no guard firing — the case `rules/workflow.md` flagged as
untested. So the rule is: the gate keys on an active worktree session, not
on the memory path. Non-worktree sessions still owe the change a branch and
a PR (main is protected), but the *write* itself goes through.
