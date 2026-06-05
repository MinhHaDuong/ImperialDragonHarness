---
name: project-archive-move-record-only-outputs
description: Live experiments/outputs/ dirs are record-only since edda724b; raw replies live in experiments/archive/outputs/ — any rule/script reading raw data must point at archive
metadata: 
  node_type: memory
  type: project
  originSessionId: f2d5c6fe-e355-4bbd-a8e7-8cba453c7d7b
---

Since commit edda724b (2026-06-04 era), `experiments/outputs/<dir>/` holds only `.record.json` pointers (+ `exp1_batch2/` which kept 140 live data files, and `sota_exp3_arm*_batch1/` with data in `run*/` subdirs). Raw model replies (CSV/JSON) live in `experiments/archive/outputs/<dir>/` — tracked P1 outcomes per the 0405 policy.

Consequences:
- Makefile rules and scripts reading raw replies must use `archive/outputs/` paths (0417 fixed tabulate_source_grounding; 0421 fixed tab_coherence + self-consistency scorer).
- A `$(wildcard outputs/...)` that expands empty while the archive sibling is non-empty is the signature of this breakage class — standing guard ticketed as 0423.
- `reconciliation_*.csv` files were gitignored (c14136ff) and never archived: `tab_decomposition_fix.tex` is FROZEN in `FROZEN_ALLOWLIST` (tests/test_makefile_dag.py); restoration tracked by [[0424]] with a 0383 caveat (scorer changed since, regen will not be byte-identical).
- Scripts filtering `measurements.jsonl` rows by path-string prefix (e.g. `tabulate_exp1_cost_summary`) are NOT affected — they match strings, not the filesystem.
