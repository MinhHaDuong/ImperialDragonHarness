---
name: project-structured-dirs-registry
description: experiments/Makefile uses hardcoded STRUCTURED_DIRS list; new sweep output dirs must be added there or extract is skipped
metadata: 
  node_type: memory
  type: project
  originSessionId: 61156091-0161-4b75-a070-0798f4d69f07
---

`experiments/Makefile` extracts CSVs from raw model JSONs via a hardcoded list:

```makefile
STRUCTURED_DIRS := census multiturn web rag \
                   decomposed decomposed_v2 sourced frontier \
                   ablation/direct/p1_base ablation/direct/p1_composite
```

**Why:** Discovery-by-glob would over-extract into archived / experimental subdirs. The list is a deliberate registry.

**How to apply:**
- When a new sweep config in `experiments.toml` writes to a new `output = "outputs/..."` directory, also add the leaf path to `STRUCTURED_DIRS` — or `make extract` will silently skip it.
- `iter_model_replies` uses non-recursive `Path.glob("*.json")` so the registered path must be the **leaf** dir, not a parent.
- The orphan-eval fallback in `evaluate-all-records` uses `outputs/*/*/*-run*.json` (2-level glob since PR #342) — if a sweep writes 3 levels deep, that glob also needs updating.
- This rule plays directly with [[project-exp1-module-scheme]] (where the sweep output paths live).
- Long-term fix: refactor to discovery-based extract (related: [[project-rename-ablation-to-exp1]] if filed).
