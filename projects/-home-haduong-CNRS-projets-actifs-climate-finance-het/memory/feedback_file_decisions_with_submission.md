---
name: feedback-file-decisions-with-submission
description: "Journal editorial decisions / referee reports are filed beside the submission they decide on, as tracked diffable text — not a new release folder, not a PDF"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d8b4bfb4-717a-4dfc-9659-8493698628b2
---

A journal's editorial decision or referee reports are archived **inside the
existing `release/<date> <venue>/` folder of the submission they decide on**, as
tracked, diffable text (`.md`/`.txt`) — e.g.
`release/2026-03-18 Oeconomia/referee-reports.md` (PR #809). Never create a new
dated `release/` folder for the decision, and don't track the received PDF/email.

**Why:** A decision belongs with the submission it judges; the precedent is
`release/2026-01-14 Special Issue.../20260216 decision.txt` sitting beside its
submission. Tracked text is diffable, greppable, and feeds the response-to-
reviewers / R&R version-ladder workflow ([[project_oeconomia_rr_pipeline]]); a
binary PDF is none of those. (Author corrected an initial plan that proposed a
new release folder.)

**How to apply:** Extract the text from the source PDF (`pdftotext -layout`) into
Markdown in the submission's folder. **Verify the extraction is token-complete
against the source before the original is removed** — and leave deleting the
source file to the author; don't delete it yourself. The convention is proposed
as a harness rule in IDH ticket 0264 (PR ImperialDragonHarness#421).
