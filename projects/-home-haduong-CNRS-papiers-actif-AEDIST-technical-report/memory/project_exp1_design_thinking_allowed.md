---
name: project-exp1-design-thinking-allowed
description: "Exp 1 (parametric baseline) allows thinking; the design constraint is no-web, enforced via system_instruction. Thinking is part of the parametric capability being measured."
metadata: 
  node_type: memory
  type: project
  originSessionId: 05a0aece-0924-408e-95ce-e06061312fc0
---

Exp 1 (`sweep_ablation_p1_direct_base`, model set `modelset_ablation_journal`) measures the best row-level F1 achievable from model memory alone. The design constraint is **no web search**, enforced via the sweep's `system_instruction` ("You have no web search capability..."). **Thinking is allowed** — CoT is part of the model's parametric capability and counts toward the F1 ceiling.

**Why:** Confirmed by user 2026-05-21. The journal panel includes `qwen/qwen3-max-thinking`; the sweep does not set `no_think=true` and is correct not to.

**How to apply:**
- Do not propose `no_think=true` for Exp 1 sweeps.
- The preliminary classification table in [[project_seed_silentdrop_bug]] / ticket 0138 listed `direct_complete / direct_extract` as Class A (thinking-off preferred). That label is **wrong for Exp 1**. Class A may still hold for RAG-grounded extraction sweeps where CoT wastes evidence-anchored tokens — verify per sweep, do not generalise from the table.
- For the journal panel, only `qwen/qwen3-max-thinking` is thinking-capable. The other thinking-capable models (`kimi-k2-thinking`, `ernie-4.5-21b-a3b-thinking`) live in different sweeps (regimes scatter, SOTA frontier) — don't conflate.
