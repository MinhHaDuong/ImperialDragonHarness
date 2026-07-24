---
name: feedback-judge-lineup
description: "Final 3-judge lineup for pool→judge pipeline, locked after 7 smokes across 9 model families"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 207f5efc-4fd9-4bf1-b8ef-21487b529294
---

The LLM-as-judge lineup for `scripts/judge_pool.py` (GENERATION.md §3.2 6-dim rubric) is locked to three models from three distinct families, with no overlap with the SOTA generator lineup:

- `anthropic/claude-sonnet-4.6` — 4s/voice, full 1→3 variance, consistent
- `google/gemini-2.5-pro` — 55s/voice (needs `reasoning.exclude=true` + `max_tokens=24000`), full 1→4 variance, drives Top-1 in 3/7 voices in censorship simulation
- `openai/gpt-5.4-mini` — 4s/voice, clean 190-token output, no reasoning visible

**Why:** Empirical smoke on 5 auteur candidates across 9 candidate models. Excluded models with specific failure modes:
- `gemini-2.5-flash` / `gemini-3-flash-preview` (non-lite): **inverted scoring** vs 5-judge consensus — declared the worst candidate the best
- `kimi-k2.6`, `minimax-m2.7`: empty output (reasoning burn even with `exclude=true`)
- `nemotron-3-super`: 133s + JSON duplicate bug
- `step-3.5-flash`: refuses JSON format
- `owl-alpha`: uniform/suspect scores
- `gemini-2.5-pro` is expensive at $1.25/$10 per Mtok but removing it changes Top-1 in 3/7 voices and drops survivor count below 6 for ada/curie. Keep it for editorial fidelity (~$0.30/voice).

**How to apply:** When extending the pipeline to new voices or testing judge replacements, re-smoke on a 5-candidate subset before committing. The `JUDGE_OVERRIDES` dict in `scripts/judge_pool.py` is the place to wire per-judge reasoning configs (mirror the pattern from `MODEL_OVERRIDES` in `smoke_sota_or.py`). Same-family overlap with generators creates auto-preference bias — avoid.

**Empirical verdict (bench v3, post-fan-out 9 SOTA + LoRA on 1194 candidates):** Anthropic Opus 4.6 is the clear winner *as generator* (moy 3.10, Σ 78 ors — more than the next two combined). This is consistent with reviews flagging 4.6 as the literary variant vs 4.7 (more verbose, more literal). The judge panel (Sonnet 4.6 + Gemini 2.5 Pro + GPT-5.4-mini) shows no obvious auto-preference toward Sonnet's own family — Sonnet judges Opus 4.6 generations highly along with the other two judges. See `generations/coda-notes.md` for the full medal table and Σ ors per source.

Related: [[feedback-soft-cap-aggregation]], [[feedback_max_tokens_runaway]], [[project-lora-negative-result]].
