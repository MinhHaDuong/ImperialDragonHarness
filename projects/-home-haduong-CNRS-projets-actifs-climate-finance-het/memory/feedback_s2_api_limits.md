---
name: S2 API offset and retry limits
description: Semantic Scholar search API caps at offset 1000 and returns 504s under load — script was fixed in PR #263
type: feedback
---

S2 `/paper/search` endpoint requires `offset + limit ≤ 1000`, not ~10K as originally coded. Also 504 Gateway Timeouts are common under sustained querying.

**Why:** First harvest attempt crashed at offset 1000 with 400 Bad Request; second attempt crashed with 504 before retry logic was added.

**How to apply:** When modifying `catalog_semanticscholar.py`, remember the 1000-result cap per query. For broader coverage, would need the S2 bulk download API (different access tier). The retry logic now handles both 429 and 5xx errors.
