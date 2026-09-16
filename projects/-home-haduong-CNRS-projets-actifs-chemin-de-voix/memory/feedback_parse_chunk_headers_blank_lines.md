---
name: parse-chunk-headers-blank-lines
description: "parse_chunk_headers() stopped at first blank line, silently dropping lang/score tags — caused 0 training texts for 7+ voices"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c6993323-a57f-4a65-b705-7ca0dc0d124f
---

`select_dataset.py:parse_chunk_headers()` originally stopped reading at the first blank line. Chunk files have TWO header sections separated by a blank line — the second section contains `# language:` and `# score:` tags. Stopping early left these fields as empty strings.

**Why:** `train_lora.py` filters manifest entries by `rec.get("lang") != lang`, so entries with `lang=''` were silently excluded. Result: 0 training texts loaded for every voice whose manifests were regenerated with this bug. Manifests looked syntactically correct but were functionally empty.

**How to apply:** If `train_lora.py` loads 0 docs for a voice, check `parse_chunk_headers()` in `select_dataset.py` first. The fix is: skip blank lines instead of stopping at them (`if line.strip() == "": continue`). After fixing, regenerate all manifests. Also check `extract_mistral_ocr.py`'s `_split_markdown()` for the same guard pattern (fixed in PR #107).

**Related:** [[cjk-word-count]] — same family of silent-failure bugs in word-count guards.
