---
name: feedback-real-billing-not-estimates
description: "For cost analysis, use real OpenRouter billing (dashboard or activity log), not estimates from $/Mtok × token counts."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de6d8e24-6965-414a-a4b6-ec52fd3b55dc
---

For LLM-cost analysis in this project, **use OpenRouter's real billing data**, never compute cost from `$/Mtok` rates × stored `prompt_tokens`/`completion_tokens`.

**Why:** when offered an agent-scraped per-token price table during the medal-tally cost work (2026-05-19), user replied "En fait il faut mieux la facture réélles de OR, tient compte des tok vrais" and pasted the OR dashboard / activity log directly. The hallucination risk from web-scraping pricing pages is real (an Anthropic-cutoff agent will guess at modern model slugs and prices) and the real invoice is already authoritative — provider-side reasoning tokens, cache discounts, route-level pricing variations are all baked in.

**How to apply:** the durable source-of-truth file is `config/openrouter_spend.yaml` (per-model `spend_usd`). To refresh it:

- Dashboard view groups models on their own line when spend is non-trivial; smaller spend goes into `Others` and aggregated slugs like `DeepSeek V3.2` may bundle multiple actual models.
- For models bundled in `Others`: filter by model in the OR **activity log** (`https://openrouter.ai/activity`) and sum per-call costs. NB: the activity view may paginate — flag as "lower bound" if visible count < bench-manifest count.
- Don't trust LLM agent output that claims to have fetched current OR prices without a verifiable WebFetch trace.

See [[reference-openrouter-billing]] for the data-source map.
