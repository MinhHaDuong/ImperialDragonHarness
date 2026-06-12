---
name: pipe_table_splitting
description: Pipe table extractor must split on non-pipe gaps to handle multi-table responses (frontier models)
type: feedback
---

When responses contain multiple pipe tables (e.g., frontier models produce sector overview + plant inventory + summary tables), the extractor must split them into separate candidates and score each independently. Merging all pipe tables into one CSV causes the first table's header to dominate, rejecting plant inventory rows.

**Why:** Frontier/deep-research models produce long structured reports with 5-11 pipe tables. The plant inventory table is rarely the first one.

**How to apply:** Any code that parses pipe tables from model responses should handle multiple tables per response. The scoring function then picks the best candidate (usually the plant inventory based on header keywords and row count).
