---
name: project-experiment-costs
description: Total API costs per experiment run as of 2026-05-25
metadata: 
  node_type: memory
  type: project
  originSessionId: b80ae846-ed78-4277-896e-c92fcf657a58
---

Costs queried from raw output JSON files on 2026-05-25.

| Experiment | Source dirs | Cost |
|---|---|---|
| Exp 1 (16 models × 5 reps) | `experiments/outputs/exp1_batch2/` | $2.85 |
| Exp 3 arm 1 — naive | `experiments/outputs/sota_exp3_arm1_batch1/` | $12.97 |
| Exp 3 arm 2 — optimised | `experiments/outputs/sota_exp3_arm2_batch1/` | $14.48 |
| **Exp 3 total** | | **$27.44** |
| **Grand total (Exp 1 + Exp 3)** | | **$30.29** |

Exp 3 arm 2 cost field is `total_cost_usd` inside a list-of-dicts per `summary.json`.
Arm 2 costs more than arm 1 because multi-turn optimised runs accumulate context across turns.

**Why:** Arm 2 (optimised) uses a multi-turn state machine; each turn's accumulated context increases per-call token count vs. the single-shot arm 1 naive prompt.

**How to apply:** Use for budget reporting and cost-per-output comparisons in slides/manuscript. See [[project-exp1-done]] for exp 1 detail.
