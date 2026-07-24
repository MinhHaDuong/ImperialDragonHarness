---
name: This machine is padme
description: The current working machine hostname is padme — the GPU server where corpus data lives
type: reference
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
---
The machine running these sessions IS padme — the GPU server. Claude Code runs directly on padme; there is no remote SSH needed. `refined_works.csv` and all Phase 1 corpus data live here at `$CLIMATE_FINANCE_DATA/catalogs/`. A failing `test_corpus_acceptance.py::test_refined_works_exists` on padme is a real problem, not an expected data-missing failure.
