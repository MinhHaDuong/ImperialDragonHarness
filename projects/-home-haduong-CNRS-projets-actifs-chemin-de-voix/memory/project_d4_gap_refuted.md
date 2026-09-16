---
name: project-d4-gap-refuted
description: 2026-05-18 judge sweep refuted the cultural-notes coverage → D4 score hypothesis; ticket 0231 closed accordingly
metadata: 
  node_type: memory
  type: project
  originSessionId: be60ade1-d9f6-4a05-a08e-1874e96670c5
---

The 2026-05-18 judge sweep (Sonnet 4.6 + Gemini-2.5-pro + GPT-5.4-mini, 14 voices, ~180 candidates each) tested whether thin cultural-notes coverage depresses the D4 ("Ancrage VN") dimension. It does not.

| group | mean D4 | mean (D4 − other dims) |
|---|---|---|
| THIN (alienor 1/26, rahan 1/52, indy 4/50, manne 5/56, zhenghe 6/46) | 2.54 | +0.39 |
| THICK (9 other voices) | 2.49 | +0.36 |

D4 is the highest-scoring dim across all 14 voices. Coverage rank and D4 rank are uncorrelated — indy with 4/50 notes posts the largest D4 advantage (+0.66) in the sweep.

**Why:** 0231 was deferred 2026-05-17 with the explicit revisit trigger "if §3 judges flag systematic D4 gap on thin voices". The 2026-05-18 sweep is the first run where that trigger could be tested; result is null, so the ticket was closed without backfill (PR #147).

**How to apply:** If anyone re-raises "we should backfill cultural notes for thin-coverage voices to improve D4", cite this null result before spending the effort. The grounding signal in current generations comes from LoRA + persona + prompt verses, not from cultural-notes density. Linked to [[feedback-judge-lineup]] (judge configuration), the underlying [[project-corpus-ada-weighting]]-style coverage tables, and the closed ticket itself.
