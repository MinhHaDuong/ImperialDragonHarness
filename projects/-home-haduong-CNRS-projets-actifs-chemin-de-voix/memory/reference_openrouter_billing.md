---
name: reference-openrouter-billing
description: Where OpenRouter billing data lives and how to retrieve it for the chemin-de-voix bench cost analysis.
metadata: 
  node_type: memory
  type: reference
  originSessionId: de6d8e24-6965-414a-a4b6-ec52fd3b55dc
---

OpenRouter billing for this project has two surfaces:

- **Dashboard** (`https://openrouter.ai/activity`): aggregate per-model spend table with Min/Max/Avg/Sum columns. Two time windows offered: "week" and "all". Models with low spend bundle into `Others`. Some labels are catch-all slugs (e.g. `DeepSeek V3.2` may cover multiple deepseek variants) — verify before attributing.
- **Activity log** (same URL, scroll table): per-call rows with model, provider, app name, input/output tokens, exact cost USD. The app name "chemin-de-voix judge" appears on all calls regardless of whether the call is a judge or a generator — it's the OR app label, not the role. Filterable by model.

**API** alternative — `GET /api/v1/credits/activity` (needs the user's OR key) returns the activity log programmatically. Not yet automated in this repo; a future script `scripts/fetch_or_spend.py` would regenerate `config/openrouter_spend.yaml` from it.

The current `config/openrouter_spend.yaml` was hand-assembled from dashboard reads + per-call sums for the bench-only models that landed bundled in `Others`. See [[feedback-real-billing-not-estimates]] for the rationale (don't compute from `$/Mtok` × tokens).
