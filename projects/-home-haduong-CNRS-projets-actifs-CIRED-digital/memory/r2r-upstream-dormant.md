---
name: r2r-upstream-dormant
description: R2R (the RAG engine Cirdi self-hosts) is abandonware since ~Nov 2025; upstream team pivoted away
metadata: 
  node_type: memory
  type: project
  originSessionId: d85d05f6-f79f-4dc3-923c-6868021a8cf6
---

Cirdi self-hosts R2R by SciPhi. As of 2026-06, the open-source R2R project is effectively dormant:

- Last shipped artifact: **v3.6.6** (PyPI + Docker `latest`, 2025-08-17; added GPT-5 support). No GitHub Release was cut for it — the Releases page is frozen at v3.6.5 (2025-06-06), which makes it *look* more dead than it is.
- Last commit to `main`: **2025-11-07** (13 commits past v3.6.5 sit unreleased). Nothing since.
- Cause: the team (YC W2024, formerly SciPhi) rebranded to **Event Horizon Labs**, now "AI research lab automating all of investing" — a hard pivot off RAG.
- sciphi.ai marketing still claims "actively maintained"; the git/Docker/YC artifacts contradict it. Trust the artifacts.

**Why:** Cirdi's retrieval engine has no upstream fixes or security patches coming. This is a sustainability risk that belongs in the report's costs-and-sustainability chapter, not just an ops footnote.

**How to apply:** Newest pullable image is v3.6.6 (Aug 2025); production runs v3.6.3 — pin to `sciphiai/r2r:v3.6.6` rather than drifting on `:latest`. Treat v3.6.6 as the permanent ceiling. If Cirdi must outlive this, plan a migration to an alternative RAG stack. The embedding dependency on OpenAI is the separate single-point billing risk — see [[r2r-embeddings-openai-billing]].
