---
name: project-lp-matcher-cost
description: What the AEDIST plant-matcher uses in its MILP cost function (and what it does NOT).
metadata: 
  node_type: memory
  type: project
  originSessionId: f6f1d1a2-4c3d-4e54-b814-4c59988b5ad0
---

The plant-name-to-reference matcher in `src/aedist/matching/lp.py` is a MILP optimal-assignment solver. Its cost function is:

`cost(i, j) = base_cost(i, j) + capacity_weight · |Δcapacity_MWe|`

- `base_cost` = 0 / 1 / DEFAULT_MISMATCH_PENALTY=1000 based on a rapidfuzz `partial_ratio` name-similarity score against `DEFAULT_SIMILARITY_THRESHOLD = 90` (integer 0–100 scale).
- `capacity_weight = 0.001`, applied to absolute MWe difference.

**Province and fuel are deliberately NOT in the matching cost** — see ADR-3 (no grouping by province × fuel). They are computed post-match as cell-level attribute accuracy (`fuel_accuracy`, `status_accuracy`, `province_accuracy`) on the rows the LP picked.

**Why:** Manuscript Annex A (line 148) used to claim "fuzzy plant-name matching (`matching_threshold = 0.85`)" — wrong on three counts (algorithm understated, parameter name wrong, value wrong). Audited and corrected 2026-05-21 (PR #382).

**How to apply:** When someone asks "does the matcher use X attribute?", remember that only name+capacity feed the LP cost. Province/fuel/status come in afterward as cell-level scoring on already-matched pairs. The defaults (`similarity_threshold = 90`, `capacity_weight = 0.001`) are in `matching/lp.py` and not currently overridden anywhere in the experiment pipeline.

Related: [[reference-zotero]] (unrelated, just adjacent in memory).
