---
name: max-tokens-runaway-generation
description: clean_corpus.py needs max_tokens cap — Qwen3.5-9B enters infinite generation without it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a35f7c24-d6a7-4938-99a5-8e7811affaeb
---

clean_corpus.py had no max_tokens in the LLM request payload. Qwen3.5-9B with `--reasoning off` still generated 16K+ tokens for some inputs (cleaning task), filling the 65K context window at ~4 tok/s (90+ min per file). Fixed with MAX_OUTPUT_TOKENS=16384.

**Why:** Without the cap, the model enters repetition loops on certain inputs. Previous sweep succeeded because most files triggered EOS normally — the issue only surfaces on specific problem files. Also: generation speed at ctx=65536 with f16 KV on A4000 is ~4 tok/s (not the ~30 tok/s expected), likely due to KV cache pressure.

**How to apply:** Always set max_tokens when calling local LLMs for corpus processing. For cleaning tasks, 16K is a safe cap (cleaned text should not exceed input). Monitor `/slots` endpoint `n_decoded` and `n_remain` to detect runaway generation early. Consider reducing `--ctx-size` to 16384 or 32768 for cleaning tasks (most chunks are 2-5K tokens) — 65536 with f16 KV on A4000 drops generation to ~0.5 tok/s on long sequences.
