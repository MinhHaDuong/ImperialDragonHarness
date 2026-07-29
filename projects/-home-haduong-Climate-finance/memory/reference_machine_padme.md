---
name: This machine is padme
description: The current working machine hostname is padme — the GPU server where corpus data lives
type: reference
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
modified: 2026-07-29T17:49:37.659Z
---
The machine running these sessions IS padme — the GPU server. Claude Code runs directly on padme; there is no remote SSH needed. `refined_works.csv` and all Phase 1 corpus data live here at `$CLIMATE_FINANCE_DATA/catalogs/`. A failing `test_corpus_acceptance.py::test_refined_works_exists` on padme is a real problem, not an expected data-missing failure. Exception (2026-07-29): `test_reranker_cache_exists` fails in a *worktree* because `llm_relevance_cache.csv` is DVC-untracked and never reaches worktrees (ticket 0592) — check the primary checkout before declaring the data missing.
