---
name: Ollama num_ctx via native API
description: Ollama /v1/ endpoint ignores num_ctx — must use native /api/chat with options.num_ctx
type: feedback
---

Ollama's OpenAI-compatible `/v1/chat/completions` endpoint silently ignores `num_ctx` passed via `extra_body`. It defaults to 32768 and truncates silently. Must use native `/api/chat` endpoint with `options.num_ctx` to control context size.

**Why:** Discovered when all local RAG results had `prompt_tokens=32768` despite corpus being ~70K tokens. Cloud models reported 55K-74K for the same content.

**How to apply:** When querying Ollama models, use `query_ollama_native()` from harness.py instead of `query_single_turn()`. Set `num_ctx` to actual need (e.g., 81920 for our corpus), not model max (131072) — saves KV cache VRAM and avoids CPU offload.
