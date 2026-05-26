---
name: feedback-presence-metrics-saturate
description: "Presence-based quality metrics (source present, COD present, field complete) trivially saturate to 1.0 in parametric Exp 1 because models fill every column they're prompted for, even with hallucinated values."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba2d67f0-75cd-40df-9a2d-f526a12356d8
---

In Exp 1 (parametric, no web, no documents), models fill ALL columns the prompt requests with plausible-looking but hallucinated content. Presence-based metrics (`source_presence`, `high_conf_dual_source`, `field_completeness_core`) therefore read 1.0 for every run — not a scoring bug, a structural property of the setup.

**Why:** Caught in ticket 0348 when spider axes showed uniformly 1.0 for several dimensions while slide 4 was showing clear hallucination evidence. The fix was to replace presence metrics with discriminating metrics: source diversity (distinct sources), source spread (Herfindahl-like concentration), COD plausible (year in valid range, collapsed to 0 if all identical).

**How to apply:** When designing quality axes for parametric/memory-only conditions, test against actual data before committing to metrics. Any metric that measures "did the model write anything there" will saturate. Prefer metrics that measure "did the model write something *different* across runs" or "did it write something *valid*."
