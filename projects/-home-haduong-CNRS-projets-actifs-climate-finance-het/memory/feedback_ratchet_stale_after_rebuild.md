---
name: feedback_ratchet_stale_after_rebuild
description: A green prose-ratchet suite does not mean the ceilings match the current manuscript — a base rebuild leaves them stale.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5c2eb28b-c873-418d-84d4-87a2446adaf8
---

The prose ratchets (`tests/test_manuscript_prose.py`, ceilings in
`tests/data/*_ceiling.txt`) only assert `count <= ceiling`. A green suite means
the manuscript is *under* the ceiling, not *at* it. After the v2.0.5 base rebuild
from the French VF (0172/0173) replaced the entire prose, the em-dash ceiling
still read 132 and define-by-negation 20, while the rebuilt `body()` carried 0 of
each — the ceilings were baselined against the pre-rebuild draft and never
re-cut. Tickets 0134/0162 read as "rewrite the prose"; the actual work was
re-baselining the stale guards (PR #935: em-dash 132→0, cap 4→2, define-by-neg
20→3).

**Why:** a ratchet is a backslide guard, not a current-state report; a big base
rewrite silently opens huge slack that no test flags.

**How to apply:** after any manuscript base rebuild, measure every ratchet's
*actual* count in `body()` and re-cut each ceiling down to it (or to the
`config/ai-tells.yml` documented budget where you want to leave the author room —
e.g. define-by-negation to `max_per_document: 3`, not 0). Distinguish genuine
stale slack (132 vs 0) from intentional design headroom (conditional_words 5 vs
3 is fine). Don't trust a green suite to mean "minimal". Related:
[[feedback_caps_force_pruning_not_compression]] (report actual, don't game the
number).
