---
name: handoff-in-state-not-tickets
description: "Session/supervision handoffs go in STATE.md + MASTERPLAN + ticket DAG edges, never in a tracker ticket"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6f02f069-f31e-43f6-bcdd-4f9798d60570
---

When preparing a cross-session or cross-machine handoff (supervision moving to
padme/web, end-of-day checkpoint), encode it in the standing orientation
files: current state and standing authorizations in `STATE.md`, milestone
narrative in `MASTERPLAN.md`, and work sequencing as `Blocked-by:` edges in
the ticket DAG. Do NOT file a "handoff/orchestration tracker" ticket.

**Why:** The author rejected ticket 0545 ("Not a ticket. Handoff in STATE,
MASTERPLAN and the ticket DAG", 2026-06-11). Tickets are units of work with
exit criteria; a handoff is orientation state. The standing files are loaded
at session start via hook, so any new session gets the handoff for free —
a tracker ticket duplicates them and goes stale.

**How to apply:** wave/sequencing → Blocked-by edges (one line per
dependency); authorizations and critical path → STATE.md Next actions;
milestone context → MASTERPLAN subsection. Related:
[[merge-review-merge-cadence]].
