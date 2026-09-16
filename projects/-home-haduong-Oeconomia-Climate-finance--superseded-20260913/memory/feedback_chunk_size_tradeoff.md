---
name: Chunk size vs LLM extraction quality tradeoff
description: Bigger chunks (20K) may hurt extraction with small models — gemma-2-27b-it produced 0 refs from Harvard FECS at 20K chunks
type: feedback
---

Increasing CHUNK_SIZE from 8K to 20K chars caused gemma-2-27b-it to extract 0 refs from the Harvard FECS PDF, which previously yielded 77+ refs at 8K chunks. The model likely gets confused with too much context.

**Why:** Bigger chunks mean fewer API calls and more context per chunk, but smaller models may not handle long prompts well. The extraction prompt asks for ALL references in the chunk — with 20K chars of dense bibliography, the model may fail to produce structured JSON.

**How to apply:** Before changing chunk size, test with the target model on known PDFs. The optimal chunk size depends on the model's effective context utilization, not just its context window size. Consider reverting to 8K chunks or using a stronger model for extraction.
