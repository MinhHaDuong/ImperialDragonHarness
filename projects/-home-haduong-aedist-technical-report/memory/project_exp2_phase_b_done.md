---
name: project_exp2_phase_b_done
description: "Exp 2 = TWO arms (naive vs optimized), 4 agents × 5 reps each; optimized Phase B done (0242); Phase C cross-eval scores BOTH arms"
metadata: 
  node_type: memory
  type: project
  originSessionId: e63dac2c-61c4-4aeb-a18b-37ac8a268c54
---

**Exp 2 has TWO arms** over the same 4 agents, each 5 reps:
- *Naive arm* — single-shot Doc-07 prompt, no scaffolding, web on. The null/comparator. Outputs: `experiments/outputs/sota_exp2_naive_arm/` (4×5=20).
- *Optimized arm* — Phase A meta-prompt + multi-turn state machine. Outputs: `experiments/outputs/sota_exp2_phase_b_full/` (4×5=20).
The naive-vs-optimized contrast is what isolates the protocol's contribution. **Phase C cross-eval scores BOTH arms** (40 subject outputs, each judged by the 3 other agents → 120 calls), plus the §1 `direct_complete/` baseline as control. Don't scope cross-eval to one arm. Rubric + scoring harness tracked in ticket 0171 (refreshed + deferred post-talk; owned by parent 0199). Phase C is post-talk work, see [[project_talk_narrative_three_plus_case_study]].

Exp 2 optimized arm Phase B full batch is complete as of 2026-05-23. All 20 runs (5 reps × 4 agents) classified `report`.

**Figure 3 delivered (PR #469, ticket 0263, 2026-05-23).** Three-panel metadata comparison (coverage, output length, cost): `fig_exp2_arms_comparison.pdf` from `tab_exp2_arms_runs.csv`. Key findings: Anthropic 18→135 rows (5×), OpenAI 126→159, Mistral reliability up but breadth down, Qwen regresses (69→13 rows). Naive arm had 4 no_report failures (Anthropic and Mistral). §4 prose updated. Phase C (F1 + cross-eval, ticket 0171) is post-conference.

**Why:** Provides the N=5 reproducibility replication for the AEDIST SOTA optimized arm, pairing against the naive arm for comparison.

**How to apply:** Canonical outputs are in `experiments/outputs/sota_exp2_brerun1/` (PR #460, ticket 0243). The older `sota_exp2_phase_b_full/` used the wrong classifier (nemotron-nano-9b-v2 at 8K chars) and had 5 routing errors — do not use it for analysis. The brerun1 batch used deepseek/deepseek-v4-pro at 16K chars, $17.58 total. Tickets 0243 and 0244 are now closed.

Model set used:
- anthropic → claude-opus-4-6
- openai → gpt-5.5-2026-04-23
- mistral → mistral-large-2512
- qwen → qwen3-max-2026-01-23
