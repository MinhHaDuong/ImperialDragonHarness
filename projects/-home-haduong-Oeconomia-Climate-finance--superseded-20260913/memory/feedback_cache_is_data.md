---
name: feedback_cache_is_data
description: DVC outputs get wiped on re-run — persistent caches must hold the actual data, not just "done" markers
type: feedback
---

Never split "what was done" from "the data itself" in DVC pipeline caches. If a done-file says a DOI was fetched but the actual rows are in a DVC output that gets wiped, the cache is lying.

**Why:** #441 regression — citations_done.csv said 22K DOIs were done, but citations.csv (DVC output) was wiped to 17 rows. Filter saw empty citation graph, flagged 9,102 papers as isolated, corpus dropped from 31K to 27K.

**How to apply:** When designing enrichment caches, make the cache file contain the actual data rows (append-only in enrich_cache/). The DVC output should be a derived view (concat + dedup), regenerable without API calls.
