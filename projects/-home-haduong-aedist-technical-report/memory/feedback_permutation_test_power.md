---
name: feedback_permutation_test_power
description: Check minimum attainable p before writing a sign-flip permutation test threshold
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e23002cf-aa34-4dee-beda-f2985d7f7231
---

For a one-sided sign-flip permutation test on n subjects, the minimum attainable p = 1/2^n. Check this before committing to a p < 0.05 threshold.

| n | min p | p < 0.05 achievable? |
|---|-------|----------------------|
| 4 | 0.0625 | No |
| 5 | 0.031 | Yes |
| 6 | 0.016 | Yes |

**Why:** Exp 3 protocol had p < 0.05 with n=4 subjects — unreachable. Caught during review before any runs were done. Fix: effect-size-only threshold (ΔF1 ≥ 0.05).

**How to apply:** When reviewing or writing a hypothesis with a permutation test, immediately compute 1/2^n. If > 0.05, either add subjects or drop the p-value criterion.
