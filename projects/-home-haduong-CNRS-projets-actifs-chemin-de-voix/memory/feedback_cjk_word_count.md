---
name: cjk-word-count-silent-failure
description: wc -w returns near-zero for CJK text — use character-based counting for token estimates
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 83001c2f-2da2-4822-9ed4-1b9adca2a799
---

`wc -w` silently returns near-zero for Chinese/Japanese/Korean text because these scripts don't use spaces between words. Applying it to a voix-zhenghe corpus of 486KB of Chinese produced "4K tokens" — the real count was 133K.

**Why:** wc splits on whitespace; CJK prose is one unbroken stream. The error propagated silently into a false "CRITICAL: below 15K floor" verdict.

**How to apply:** When estimating tokens for any corpus that may contain CJK, use character-based counting: count CJK codepoints directly (≈1 token each for Qwen-family tokenizers) + Latin words × 1.3. Python snippet:
```python
cjk = len(re.findall(r'[一-鿿㐀-䶿]', text))
lat = len(re.findall(r'[a-zA-ZÀ-öø-ÿ]+', text))
tokens = cjk + int(lat * 1.3)
```

`select_dataset.py:count_content_words()` fixed PR #100. `extract.py` (4 guards) and `harvest_corpus.py:count_words()` fixed PR #103 (ticket 0217). Remaining instances: `extract_mistral_ocr.py:136` (ticket 0219), `fetch_from_inventory.py:467,553,770` (ticket 0220). Standing regression test planned in ticket 0221.

Linked: [[per-backend-queue-scheduler]] — same class of silent numeric failure.
