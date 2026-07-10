---
name: feedback-settled-debates-to-brief
description: "A settled debate must be written into the enforced register (editorial brief) at settlement time, or it gets re-litigated"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: abeb176f-22ca-461f-bb52-7bdffd08f43b
---

2026-07-08. The Türkiye figures question (1.7 vs 15 GW, grant element) had been settled before, resurfaced in ticket 0172's phrasing ("align the discrepancies"), survived two splits (0175, 0180), and irritated the author: « c'était d'autant plus pénible qu'on avait déjà clos le débat ».

**Why:** A decision that lives only in conversation or in open-question ticket wording is invisible to future agents and tickets — each pass re-derives the "open" problem. The editorial brief (`docs/editorial-brief.md`) is the register the `/review-pr-prose` auditor checks on every diff; a settlement recorded there with a do-not-reopen clause is structurally enforced.

**How to apply:** The moment the author closes a debate, write it as a brief entry (Decision/Rationale/Ticket/Status) in the same commit, and rewrite any ticket phrasing that presents it as open. Ticket logs record history; the brief records law. See [[feedback_propagate_notes_to_tickets]] and [[project_rr_traceability_ledger]].
