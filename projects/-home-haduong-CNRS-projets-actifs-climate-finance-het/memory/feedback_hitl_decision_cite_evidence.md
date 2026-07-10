---
name: feedback_hitl_decision_cite_evidence
description: "When recording an author's HITL decision in a commit/doc/ticket, cite the evidence so a diff-only reviewer can verify it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ff9c74e-9071-4c82-b0a0-341f19c5551f
---

When you record into a commit, doc, or ticket a decision the author made in
live conversation — especially a decision the ticket explicitly marks HITL —
**cite the evidence**: quote the author's exact message ("C then.", "merge on
approve") in the commit body / doc. Otherwise an autonomous agent writing
"DECIDED: Option C (author)" is indistinguishable, to anyone reading only the
diff, from self-authorizing a HITL-only choice.

**Why:** on ticket 0161 (2026-07-08), the `/gaze` built-in reviewer read only
the PR diff, saw the ticket line "This is a HITL decision — draft options for
the author" and, ten minutes later, a commit logging "Frozen-data policy
DECIDED: Option C (author)" with no referenced artifact. It flagged this
high-severity as an agent self-closing a HITL decision. The decision *was*
genuinely the author's ("C then." in session), but nothing in the diff proved
it — a legitimate procedural catch.

**How to apply:** in the commit/doc/ticket-log line that records the decision,
name the evidence — the author's verbatim message and that it came from the
working session — so the record is self-verifying. A diff-only reviewer (or a
future you) must be able to confirm the human, not the agent, chose. Relevant
to any HITL-gated row on the R&R traceability ledger
([[project_rr_traceability_ledger.md]]) and settled-debate capture
([[feedback_settled_debates_to_brief]]).
