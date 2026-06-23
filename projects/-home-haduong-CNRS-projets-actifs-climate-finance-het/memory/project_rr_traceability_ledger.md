---
name: project_rr_traceability_ledger
description: "Œconomia R&R per-remark response ledger location + author closing discipline (no non-actionable close, HITL sign-off)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 29958ba6-cb6c-42c7-8d09-98537c33814e
---

The Œconomia round-1 R&R response is tracked per-remark in
`release/2026-03-18 Oeconomia/response-traceability.md` — a 60-row table, one
row per atomic referee remark, each pre-mapped to its owning child ticket
(0134–0143). Columns: Response / Where (manuscript §/page) / Commit / Sign-off.
Built in PR #813 for ticket 0152 (the response-to-reviewers letter).

Atomic remark count is **60**, not 56: the "~56" was an approximation; the
editor's history↔quant concern splits into a framing point + 6 method questions
+ a logical-role point, and Reviewer 2's two general paragraphs carry four asks.

**Author-set closing discipline (binding):**
- No remark is ever closed as non-actionable — there is no decline / out-of-scope
  / won't-fix disposition. A remark that resists a change keeps its row open and
  goes to the author.
- Every close is human-in-the-loop: a row counts as answered only when the author
  fills its Sign-off cell. The agent may draft Response/Where/Commit, never mark
  a row closed.

The verbatim referee text is `release/2026-03-18 Oeconomia/referee-reports.md`;
the routing source-of-truth is the 0133 tracker inventory. See [[project_oeconomia_rr_pipeline]].
