---
name: feedback-verify-real-codepath
description: Verify a fix by forcing the real code path — not an input that can be served from cache
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0b9e6aa0-015a-4ef1-af1c-fd89de5e1b2b
---

When confirming a fix, exercise it with input that forces the actual failing code path. Inputs that can be served from a cache (or any memoized/short-circuit layer) can return success while the underlying defect is still live.

**Why:** On 2026-06-23, after rotating Cirdi's OpenAI key, a *repeated* RAG query returned HTTP 200 and looked fixed — but R2R caches query embeddings, so it never called OpenAI. A *novel* query (fresh embedding) revealed the key was actually rejected (401). The cache produced a false-positive "fixed." Same trap applies to CDNs, HTTP caches, build caches, browser caches, DNS, and memoization.

**How to apply:** For any fix verified by observing behavior, vary the input enough to defeat caching (a unique/random query, a cache-busting param, a cold start, or clear the cache first). State which layer you bypassed. Pairs with the diagnosis discipline in `rules/workflow.md`: report the observation, and make sure the observation came from the real path. Related ops case: [[r2r-embeddings-openai-billing]].
