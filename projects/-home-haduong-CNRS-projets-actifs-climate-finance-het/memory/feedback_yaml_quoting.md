---
name: YAML quoting for query strings
description: Use single-quoted YAML with inner double quotes for phrase search queries in corpus_collect.yaml
type: feedback
---

Query strings in config/corpus_collect.yaml that need literal double quotes (phrase search) must use single-quoted YAML with inner double quotes: `'"climate finance"'`, not `"climate finance"` (which strips the quotes).

**Why:** #181 externalized the worldbank query as `"climate finance"` (YAML double-quoted), which sent `climate finance` (unquoted) to DSpace/Solr — a broad OR query returning 499 results instead of 192 for the phrase search.

**How to apply:** When adding or editing query strings in corpus_collect.yaml, check that phrase-search quotes survive YAML parsing. Match the istex/scopus pattern: `'"phrase here"'`.
