---
name: feedback_followup_lets_parent_close
description: "A follow-up ticket exists so the parent can CLOSE now; don't keep the parent open as a pseudo-tracker"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ff9c74e-9071-4c82-b0a0-341f19c5551f
---

When you file a follow-up ticket for residual work, the **point** is that the
current ticket can close now, with the residual carried by the new ticket. Do
not then keep the parent open "as a tracker" — that defeats the purpose and
leaves two open tickets where one delivered.

**Why:** on ticket 0161 (2026-07-08) I filed follow-up 0195 for the pipeline-run
remainder (archive the A.5 tables, reconcile the two co-citation builders), then
kept 0161 open calling it a tracking ticket. The author corrected: "the point of
a followup is that the current can close." 0161's own exit criteria — audit
complete, every cited stat shown reproducible, frozen-data policy recorded — were
already met by the merged PR; the archiving/reconciliation was **new** follow-on
hardening, not an unmet 0161 criterion.

**How to apply:**
- Before calling a ticket a "tracker," check: are ITS exit criteria met? If yes,
  close it and let the follow-up own the new work. A ticket closes when its own
  criteria are met, not when every downstream nicety is done.
- "Tracking-style" describing the *work* (an audit surveying many items) does NOT
  mean the ticket spawns children that must all close first. A genuine tracker is
  one whose exit criterion IS "all children closed" (e.g. [[project_rr_traceability_ledger]]
  tracker 0133). Most tickets are not that.
- If the closing PR should close the ticket, use `**Ticket:** …` (not
  `Ticket-ref:`). Reserve `Ticket-ref:` for genuinely-still-open tickets.
- Distinct from [[feedback_pr_creates_ticket_no_close]] (a PR that *files* a
  follow-up uses Ticket-ref for the follow-up) — here the point is the PR still
  closes its OWN parent ticket.
