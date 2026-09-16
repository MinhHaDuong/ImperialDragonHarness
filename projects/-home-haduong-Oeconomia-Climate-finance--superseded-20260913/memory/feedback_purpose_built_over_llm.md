---
name: Purpose-built tools over LLM for structured tasks
description: GROBID (5ms/cit) beat all LLM approaches (300ms-2000ms) for citation parsing — search for domain tools first
type: feedback
---

For structured extraction tasks (bibliography parsing, entity recognition), search for purpose-built ML tools before reaching for LLMs.

**Why:** Session wasted 30+ minutes benchmarking Ollama models (qwen3.5 0.8b broken, 9b thinking tokens, mistral-small too slow at 2s/query). GROBID solved the same task at 5ms/query — two orders of magnitude faster, no API cost, gold-standard quality. User had to push: "let's be dogs about that" and "why not GROBID?"

**How to apply:** When facing a data extraction task, first ask: "is there a domain-specific tool for this?" Check GROBID (bibliography), spaCy (NER), tesseract (OCR), etc. before defaulting to LLM prompting.
