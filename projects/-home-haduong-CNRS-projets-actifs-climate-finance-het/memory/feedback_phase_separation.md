---
name: Phase separation in Makefile
description: make manuscript must never trigger Phase 1 enrichment scripts or API calls
type: feedback
---

`make manuscript` (Phase 3) must be pure rendering: only `compute_stats.py` + `quarto render`. No API calls, no Phase 1 caches required.

**Why:** Phase 1 enrichment caches (`citations.csv`, OA status) may not exist on analysis-only machines. Transitive Makefile dependencies silently pulled in `export_corpus_table.py` (OpenAlex API), `build_het_core.py`, and other Phase 2 analysis scripts during what should be a fast render.

**How to apply:** When adding Makefile dependencies, trace the full chain to verify no Phase 1 artifact is reachable from Phase 3 render targets. Use per-document include/figure/table lists (not wildcards). If `compute_stats.py` reads a file, that file becomes a transitive dependency of every document — only add it if the manuscript actually uses the resulting variable.
