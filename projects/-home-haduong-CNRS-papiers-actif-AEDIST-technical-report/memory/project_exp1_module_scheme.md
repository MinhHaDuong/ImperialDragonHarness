---
name: project-exp1-module-scheme
description: "Prompt modules restructured to numbered scheme 1-6, A-D; Experiment 1 baseline = modules 2+5"
metadata: 
  node_type: memory
  type: project
  originSessionId: deab15ae-916a-4088-89c1-cfb8a32815c8
---

Prompt modules in `experiments/prompts/modules/` renamed from flat ad-hoc names to a numbered scheme:
- 1_persona, 2_goal, 3_overview, 4_narratives, 5_table, 6_bibliography
- A_Statistics, B_Temporality, C_Uncertainty, D_Completeness

Old names (base, persona, overview, narratives, statistics, bibliography, sourcing_ground, citation_columns, observed_vs_projected, pdp_completeness, data_quality_table) deleted.

**Experiment 1 baseline = modules 2 + 5** (goal + table, no persona). Rationale: keeps the ablation zero-point clean so persona's effect is measurable by comparing p1_base vs p1_composite.

**Why:** User rewrote modules with cleaner structure; Experiment 1 needed a bounded, lean baseline that addresses ChatGPT reviewer ask 1 (not designed to fail, explicit scope).

**How to apply:** When editing or referencing modules, use new numbered names. Before running Experiment 1 sweep (ticket 0177), update `harness.py` `_MODULE_ORDER` and `modules/README.md` to reflect new names (ticket 0175 scope).
