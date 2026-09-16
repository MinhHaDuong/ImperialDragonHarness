---
name: empty-threshold-false-negatives
description: clean_corpus.py EMPTY threshold (default 0.3) now configurable via --min-ratio; was hardcoded 30%, rejects valid heavy-cleaned content
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a35f7c24-d6a7-4938-99a5-8e7811affaeb
---

`clean_corpus.py` marks a chunk EMPTY (not written, stays retriable) when `len(response) < len(body) * 0.3`. This is a false negative for two types of content:

1. **Short proclamations / short texts**: chunk body inflated by Wikisource metadata headers; the ~1KB actual prose is <30% of the 4.6KB chunk. Example: HCM's *Lời kêu gọi toàn quốc kháng chiến* (978 chars, 21% ratio).

2. **Sutta+commentary chunks**: canonical sutta text (not the author's voice) dilutes the ratio; TNH commentary is only ~22% of a 38KB chunk that includes the full sutta.

**Why:** The 30% threshold was hardcoded. Fixed 2026-05-15: `--min-ratio R` CLI flag added (default 0.3, backward-compatible). Use `--min-ratio 0.04` for heavily-cleaned content.

**How to apply:** Pass `--min-ratio 0.04` to `clean_corpus.py` for sutta+commentary or OCR-dense PDFs. As a last resort, re-run the LLM via a direct `httpx` call and write the clean file + manifest entry manually. Accept any response >20 chars as valid. Template:
```python
with httpx.Client(timeout=900) as client:
    r = client.post(f"{BACKEND}/v1/chat/completions", json=payload)
    response = r.json()["choices"][0]["message"]["content"].strip()
    if len(response) >= 20 and response.upper() != "SKIP":
        dest.write_text(f"{headers}# cleaned-by: llama-server\n\n{response}\n")
        write_manifest(manifest_path, path.name, "clean")
```
