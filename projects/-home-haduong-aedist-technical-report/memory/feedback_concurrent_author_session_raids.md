---
name: concurrent-author-session-raids
description: Expect a second author session raiding the same repo mid-raid; re-verify ticket state on origin/main before every execute launch
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d1557082-ceb0-4d01-98e8-47f3a8cd1b5e
---

During the 2026-06-05 night-queue raid, the author ran a parallel interactive
session that merged PRs (#738 0403, 0425 closure), added blockers
(0254 ⊣ 0383, 0413 ⊣ 0431+0383), opened tickets (0430/0431/0434/0435), and
refreshed STATE — all while my raid was mid-wave. Selection-time state goes
stale within minutes.

**Why:** A raid's Select/Imagine snapshot is not a reservation. Half my queue
was delivered or re-blocked by the parallel session before Execute reached it.

**How to apply:**
- Before EVERY execute-agent launch: `git fetch` + `git cat-file -e
  origin/main:tickets/NNNN-*.erg` (open?) and check `tickets/closed/` (done?).
- Keep the fetch-scan no-op gate in every execute prompt — it turned a
  would-be duplicate PR for 0403 into a clean no-op with evidence.
- Never clean worktrees/branches you don't recognize: `git worktree list`
  showed the sibling session's agents (ticket/0383, 0416, 0430…) — touching
  them would have destroyed live work. Only remove worktrees whose agentId
  you spawned. See [[killed-agent-salvage]].
- Ticket-store conflicts on rebase = the union pattern: keep both sides' log
  lines, keep upstream's Blocked-by headers. See
  [[erg-close-bookkeeping-conflict]].
- Avoid bundling a whole `tickets/` snapshot import into a content PR — it
  conflicts with every parallel ticket edit; import only the tickets your PR
  owns.
