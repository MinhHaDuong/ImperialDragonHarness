---
name: RePEc as potential corpus source
description: RePEc mirror (1.15M ReDIF files) could be harvested for economics working papers not in OpenAlex
type: reference
---

RePEc has a mirror system with 1.15M ReDIF metadata files. Could be ingested into a SQLite index and queried for climate finance working papers — especially pre-publication economics papers and working paper series (NBER, CEPR, World Bank Policy Research) that OpenAlex may index late or incompletely.

**Why not done:** Requires resyncing the 2013 mirror, building an ingest pipeline, and deduplicating against OpenAlex. Low priority given OpenAlex's improving coverage of working papers.

**How to apply:** If a reviewer asks "why no RePEc?" or if economics working paper coverage seems thin, this is the path. Not planned for v1.1.
