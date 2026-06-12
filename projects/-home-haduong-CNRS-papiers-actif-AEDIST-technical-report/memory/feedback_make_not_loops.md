---
name: Make not loops for experiments
description: Use Makefile dependencies instead of shell loops for experiment pipelines
type: feedback
---

Use Makefile to manage experiment pipelines, not shell for-loops.

**Why:** Makefile gives proper dependency tracking (rerun when model list or prompt changes), parallelization (`make -j`), incremental rebuilds, and declarative structure. Shell loops are opaque and don't track what needs regeneration.

**How to apply:** Each experiment output should be a Make target depending on its inputs (models.yaml, prompt file, script). Use pattern rules. Let `make -jN` parallelize queries. Commit and push before running long pipelines.
