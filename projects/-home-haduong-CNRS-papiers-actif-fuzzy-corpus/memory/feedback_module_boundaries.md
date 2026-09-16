---
name: Module boundary rule — no cross-script imports
description: Private symbols in scripts must not be imported by other scripts; promote to src/ instead
type: feedback
originSessionId: a7cb726a-d727-46e8-aad7-fe4efa2bc46e
---
Keep business logic in `src/fuzzy_corpus/`, not in `scripts/`. Scripts are entry points only.

**Why:** Two review rounds were needed to catch `run_wp7_conditioning.py` importing `_sample_works` from `run_wp7` via `sys.path` manipulation. Private cross-script imports are untestable and break when scripts are refactored independently.

**How to apply:** When a script defines a function another script needs, move it to the appropriate `src/fuzzy_corpus/` module immediately — not "later". LaTeX renderers → `benchmark.py`; data loading helpers → `ingest.py`; seed construction → `seed.py`.
