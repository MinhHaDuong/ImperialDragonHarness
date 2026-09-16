---
name: project-exp1-done
description: Experiment 1 parametric baseline closed 2026-05-21; 16 models × 5 reps = 80 rows in p1_base
metadata: 
  node_type: memory
  type: project
  originSessionId: f4537f72-6ba0-4e22-b885-a15b15f10ed9
---

Experiment 1 (parametric baseline, sweep_ablation_p1_direct_base) is closed end-to-end as of 2026-05-21. Final journal-v2 lineup is 16 models × 5 reps = 80 rows in `experiments/outputs/ablation/direct/p1_base/`:
- 77 status=ok / 3 declined (all GPT-5.5) / 0 error / $2.85 total
- Cost summary reproducible via `make exp1-cost-summary` (generates `report/inputs/generated/tab_exp1_cost_summary.tex` from `src/aedist/tabulate_exp1_cost_summary.py`)
- Tickets 0174 (umbrella), 0175, 0176, 0177, 0181, 0182, 0184 all closed; 0179 closed in passing; 0183 (httpx timeout) still open
- Ticket 0178 (manuscript update) merged as PR #371 on 2026-05-21. Manuscript §1 Results paragraph and slides Épouvantail frame now carry actual numbers.
- **Reasoning column dropped from Annex A** (PR #379 / ticket 0197, 2026-05-21). The "yes/no/minimal" labels described registry metadata, not per-call measurement; the harness was stripping `usage.completion_tokens_details` so reasoning_tokens were never recorded. Probe data showed `qwen3-max-thinking`, `mistral-small-2603`, `claude-opus-4.6` all produced 0 reasoning_tokens via OpenRouter when no `reasoning_effort` was sent (counterintuitive: see [[project-openrouter-reasoning-effort]]). PR #379 fixed the capture path; ticket 0198 drafts the small-N (canary + 2-rep) rerun to restore the column with empirical data, deferred per the slide deadline.

**Why:** the conference is 2026-05-27 (six days out). The data is locked and reproducible; the bottleneck is now writing.

**How to apply:** future questions about "what's in Exp 1" should read measurements.jsonl rows filtered by `result_file starts with experiments/outputs/ablation/direct/p1_base/ and not /p1_base.pilot/`. Don't recompute the lineup from registry — it's pinned in `experiments.toml [sets.modelset_ablation_journal]`.
