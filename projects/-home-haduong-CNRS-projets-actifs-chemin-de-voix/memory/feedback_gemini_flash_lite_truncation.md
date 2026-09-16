---
name: feedback_gemini_flash_lite_truncation
description: google/gemini-3.1-flash-lite truncates large chunks (>30KB body) — outputs only the tail fragment instead of full text
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 345674d2-e23b-4c8c-9a44-2efa24b95106
---

`google/gemini-3.1-flash-lite` on OpenRouter truncates large inputs: for bodies >30KB, it outputs only the last ~1-5% of the text rather than the full cleaned content. This is intermittent but reproducible on TNH story chunks (35KB) and Feynman physics essays (38KB).

**Why:** The model appears to have an effective output length limit or attention failure on large contexts despite the 16K max_tokens cap. Other gemini-lite-sized chunks (<20KB) clean correctly.

**How to apply:** After a bulk gemini-lite pass, run a ratio check: `resp_bytes / body_bytes < 0.2` on files with `body > 5KB` flags truncated outputs. Use `meta-llama/llama-3.3-70b-instruct` as fallback for those files — it handles large chunks correctly but may add a preamble sentence ("Since the provided text...") that needs to be stripped manually from the response (between `# cleaned-by:` and the actual content).
