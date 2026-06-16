---
name: feedback_shell_timeout_no_loops
description: "Shells stall on network/CI calls — wrap every gh/git call in timeout, never write shell poll-loops"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

In this environment (background sessions on doudou), shell commands **tend to stall** on network/CI calls — `gh pr view/checks/merge`, `git fetch/push`, `erg-pr-merge`. Two rules:

1. **`timeout N` on every network call** (`timeout 30 git fetch`, `timeout 25 gh pr checks`, `timeout 90 ~/.claude/skills/merge/erg-pr-merge`). An unwrapped call can hang the whole shell.
2. **No long-running shell poll-loops.** A `for attempt in $(seq 1 15); do … sleep 25; gh pr checks …; done` loop hangs the moment one CI check stays `pending` or one `gh` call wedges, and then must be killed with TaskStop.

**Instead of polling loops:**
- Queue **native GitHub auto-merge** (`gh pr merge --merge --auto`, or `erg-pr-merge` which queues) — it returns immediately and lands when CI passes; check back in a later turn.
- For a genuine wait, use a **background `Bash` with an `until` condition that EXITS** (one notification), or the **Monitor** tool — not a foreground loop.
- Do merges as **bounded discrete attempts across turns**, not one mega-loop.

**Why:** 2026-06-15 reading-3 raid — a background merge loop (`seq 1 15` + `sleep 25` polling CI) stalled on a pending `build` check; had to TaskStop it and finish the merge with bounded `timeout`-wrapped commands. The author flagged: "shells have a tendency to stall … timeout, no shell loop." Relates to [[feedback_bg_merge_anchoring]] (anchor + check state before retry).
