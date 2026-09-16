---
name: agent-worktree-locked
description: "Background agent times out before committing — worktree stays locked, branch empty; how to recover"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6535bce-fc93-4a50-a534-f5364fd023c4
---

Background raid agents sometimes exhaust their context before pushing. When this happens:
- The worktree is **locked** (`git worktree remove --force` is blocked by the live PID)
- The branch exists but has no unique commits
- The agent's file edits may still be present in the locked worktree's directory

**Why:** Agent runs out of context mid-task, never reaches the commit step.

**How to apply:** When a background agent completes with a truncated summary, immediately check:
1. `git diff master...t<NNNN>-branch --stat` — if empty, branch is bare
2. Check the worktree directory directly for uncommitted edits
3. Work in the locked worktree directory (`git -C <worktree-path> add/commit/push`) — the lock only prevents removal, not use
4. Do NOT use `--force --force` to remove the worktree while the PID is alive unless confirmed stale
