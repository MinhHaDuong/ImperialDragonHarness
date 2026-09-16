---
name: feedback-dictated-constants-verify-disk
description: "When a handoff dictates a mapping/constant table, verify the target strings against the consuming data and code on disk before committing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 39826929-4e74-43b7-9102-485e4fbcae1f
---

In the 0439 session a handoff dictated the 9-stage → 6-status derivation
table. Tests proved the table was *implemented* (function reproduces the
dict) but not that it was *correct* — the six target strings had to match
`vietnam_thermal_v1.csv` and the scoring keys (`STATUS_ORDER` in
exp1_recognition.py). They did; advisor caught that this check was missing.

**Why:** self-consistent tests pass even when the constants are wrong by
construction; the mismatch would surface only at 0413 adoption, far from the
commit that introduced it.

**How to apply:** for any dictated vocabulary/mapping landing in code, grep
the consumers and `value_counts()` the data files that the targets must
match, and say so in the verification report. Sibling of
[[feedback-verify-prose-claims]] (same principle, code constants instead of
manuscript numbers).
