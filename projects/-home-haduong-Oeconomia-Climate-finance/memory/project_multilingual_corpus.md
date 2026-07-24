---
name: project_multilingual_corpus
description: Corpus is multilingual in principle — model and tool choices must support multiple languages
type: project
---

The corpus research is multilingual in principle. This constrains embedding model choice (no English-only models) and other NLP tooling decisions.

**Why:** The author's research scope is not limited to English-language literature. Even if the current corpus is predominantly English, the pipeline must not structurally exclude non-English works.

**How to apply:** When choosing NLP models (embeddings, classifiers, extractors), always prefer multilingual options. BGE-M3 chosen over nomic-embed-text-v1.5 for this reason (ticket #406).
