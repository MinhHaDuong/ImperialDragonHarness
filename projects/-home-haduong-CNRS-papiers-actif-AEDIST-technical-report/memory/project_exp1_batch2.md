---
name: project_exp1_batch2
description: "Exp1 batch2 canonical run — 14 models × 5 reps, no web search, outputs in exp1_batch2/"
metadata: 
  node_type: memory
  type: project
  originSessionId: 50c2ce3f-0238-462c-a0d3-09e18745eddd
---

Exp1 batch2 is the canonical Experiment 1 dataset (parametric ceiling, no web search).

**Models:** Anthropic×3, OpenAI×3, Mistral×3, Qwen×3, DeepSeek×2 = 14 models × 5 reps = 70 runs.  
**Output dir:** `experiments/outputs/exp1_batch2/`  
**Pipeline:** `experiments/experiment1.mk` via manager+worker job-board (`xargs -P 60`)  
**Sweep config:** `sweep_exp1_batch2` in `experiments.toml`  
**Figures:** `fig_direct_p1_base.pdf` (strip plot) and `fig_direct_cost_quality.pdf` (cost-quality scatter) — both read from `exp1_batch2/` exclusively.

**Why:** Replaced old p1_base data (mixed web-search conditions, inconsistent model set). New run enforces `web_search=false` via system_instruction for all models.

**How to apply:** When adding models to Exp1 or rerunning, use `make -f experiment1.mk WORKERS=N exp1-batch2` from `experiments/`. Incremental additions: edit `modelset_exp1_batch2` in `experiments.toml`, then re-generate (skips existing jobs) and drain.

**Dropped:** `qwen/qwen3.6-27b` — persistent null-content (HTTP 200, content=None) on OpenRouter, not retryable.
