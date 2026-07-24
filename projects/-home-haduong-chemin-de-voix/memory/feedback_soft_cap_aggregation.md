---
name: feedback-soft-cap-aggregation
description: "aggregate_judges keeps ties at rank-5 (per-judge) and rank-6 (final), not strict slicing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 207f5efc-4fd9-4bf1-b8ef-21487b529294
---

`scripts/aggregate_judges.py` softens the §4 caps of GENERATION.md:
- `select_survivors_single_judge` caps at 5 unless tied 4-count at rank-5, then extends
- `merge_judges` caps at MAX_HITL=6 unless `(gold_count, silver_count)` tally at rank-6 matches lower ranks, then extends

**Why:** User directive 2026-05-18 — "si les 5 6 7 8 9 sont tous à 0 or 5 argent on les garde tous". Strict slicing arbitrarily breaks ties that the medal-tally metric can't distinguish. HITL sees a slightly expanded shortlist instead of an arbitrary cut.

**How to apply:** When the spec in GENERATION.md §4 says "retenir les 5 premiers" or "max 6 HITL", read it as a target with tie-keeping, not a hard slice. Don't tighten back without checking with author. On the 7 voices done in this run, no rank-6 ties existed, so output was unchanged — the soft cap is a safety mechanism for future corpus-poor voices where judges converge.

Related: [[feedback-judge-lineup]].
