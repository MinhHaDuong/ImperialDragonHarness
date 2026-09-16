---
name: feedback-fp-unrecognized-not-hallucinated
description: "LP-irreconcilable FPs must be called \"non-reconnus/unrecognized\", not \"hallucinés/hallucinated\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6212fb6-ee3d-4868-97f0-3ee0685b2b17
---

LP false positives (system_only entries) have three distinct causes: LP name-variant matching failure, real plant outside reference scope, and stale parametric knowledge. Calling all of them "hallucinations" misattributes LP matcher limitations to the model.

**Why:** Spot-check of arm3 Exp 2 FPs found that several recurring FPs (Nhơn Trạch 3&4, Bà Rịa GT, Vedan) are real plants in the reference matched under different names — the LP fails, not the model.

**How to apply:** In slides and manuscript prose, use "actifs non-reconnus" / "unrecognized plants" for FP counts derived from LP reconciliation. Reserve "hallucination" for cases where the model clearly invented something (Exp 1 Haiku province-naming, gpt-oss-20b Trung Nam recursion). When labeling FP bars in figures or captions, use "unrecognized" not "hallucinated".
