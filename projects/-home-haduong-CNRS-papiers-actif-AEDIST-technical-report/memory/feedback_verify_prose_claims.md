---
name: verify-prose-claims
description: "Manuscript numerical claims must be verified against raw data, not reconstructed from summaries"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7e5c93fc-1bcf-4c10-af5d-1452e703ce1c
---

Always verify each numerical claim in manuscript prose against the raw data source (measurements.jsonl or record files) before committing. Do not reconstruct facts from summary statistics — the direction of a comparison or the identity of an extreme-value model can be wrong.

**Why:** PR #371 had two factual errors caught by /verify: "cell accuracy falls below F1" was directionally wrong (0.53 > 0.38), and "GPT-OSS-20B widest variance" was incorrect (DeepSeek V4-Flash had wider range). Both were reconstructed from summary tables rather than queried directly.

**How to apply:** Before committing any prose with model-specific claims, run a verification query against the raw data for each claim. The /verify skill does this, but catching errors earlier avoids reroll cycles.
