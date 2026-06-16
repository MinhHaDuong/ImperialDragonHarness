---
name: feedback_durable_reminder_is_blocked_open_ticket
description: A future reminder goes in an OPEN ticket Blocked-by the triggering ticket — never a note in a closed ticket.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7b53f61c-a20c-44df-a541-3fc6bab72c28
---

To leave a reminder that must fire at a future event, create an **open**
ticket with `Blocked-by: <trigger-ticket>`. When the trigger closes, the
reminder auto-unblocks and surfaces in `erg ready` at exactly the right
moment — the dependency graph does the remembering. A note in the
"Follow-ups" of a **closed/archived** ticket is a *false* reminder: closed
tickets never surface in `erg ready` and nobody re-reads them.

2026-06-16: the "manuscript v2 must cite the Zenodo concept DOI" reminder was
first parked in closed ticket 0676 — useless. Refiled as open ticket 0677
`Blocked-by: 0665` (the arXiv push, ~2 months out); when 0665 closes, 0677
becomes ready automatically. Author had to ask "did you note it to remember
in 2 months?" to catch the dead reminder.

**Why:** the ticket store has no time-based alarms; the only durable
"remember later" primitive is a blocker edge that resolves on the triggering
event. `deferred`-labelled tickets are also suppressed from `erg ready`, so
a deferred ticket is NOT a reminder either — pair the reminder with a
`Blocked-by` on the event that should wake it.

**How to apply:** reminder for "do X when Y happens" → open ticket, body =
the concrete X, `Blocked-by: <Y's ticket>`. Cross-link from the relevant
planning/tracker ticket for a second discovery path. Related:
[[feedback_orphaned_wip_is_unlanded_exit_criteria]] (closed tickets lose
their unlanded content).
