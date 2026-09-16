---
name: F1=None means non-attempt, not zero
description: f1=None in measurements.jsonl means refusal or format error; must be excluded from mean calculations with n documented
type: project
originSessionId: a8674d80-1e78-499e-aa96-f5a6a8574fb9
---
`f1=None` in measurements.jsonl is set by `_classify_orphan()` in `evaluate.py` when the model either refused to answer or produced no usable plant inventory (e.g., aggregate tables only). It is NOT a zero score.

**Why:** Ticket 0163 (2026-05-05): three frontier models (GPT-5.4, Grok 4.20, Ernie 4.5 Thinking) at F1=0.000 in argument.md were actually f1=None in the data. Treating them as zeros inflated the impression of failure and gave wrong means.

**How to apply:** When computing mean F1 or reporting "average score", always:
1. Exclude `f1=None` rows and report n_valid / n_total
2. In prose: "mean F1 ≈ 0.46 (n=9, excluding 3 non-attempts)"
3. In code: `df[df.f1.notna()].f1.mean()`, not `df.f1.mean()`

The evaluator (`_classify_orphan`) correctly classifies: refusal → "refusal", aggregate-only output → "error", both yield f1=None.
