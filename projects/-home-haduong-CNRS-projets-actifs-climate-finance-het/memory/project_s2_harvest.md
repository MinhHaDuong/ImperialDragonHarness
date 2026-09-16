---
name: S2 harvest after ISTEX rebuild
description: After #257 merges, uncomment semanticscholar stage in dvc.yaml and run S2 harvest with API key from .env
type: project
---

After #257 (ISTEX rebuild) merges, uncomment the semanticscholar stage in dvc.yaml and run the S2 harvest. API key is in `.env`.

**Why:** S2 was skipped pre-submission due to rate limits but now has an API key configured.
**How to apply:** Create a follow-up ticket or do it in the same session after #257 merge completes.
