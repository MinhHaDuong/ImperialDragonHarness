---
name: This machine is padme
description: The current working machine hostname is padme — the GPU server where corpus data lives
type: reference
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
modified: 2026-07-27T14:16:40.650Z
---
The machine running these sessions IS padme — the GPU server. Claude Code runs directly on padme; there is no remote SSH needed. `refined_works.csv` and all Phase 1 corpus data live here at `$CLIMATE_FINANCE_DATA/catalogs/`. A failing `test_corpus_acceptance.py::test_refined_works_exists` on padme is a real problem, not an expected data-missing failure.

The corpus lives in the **primary checkout only**. A git worktree's `data/`
holds `.dvc` pointer files and little else — no `catalogs/`, no
`pool/keydocs/`, no `run_reports/`. And `.env` sets
`CLIMATE_FINANCE_DATA=data` (relative), so a script run inside a worktree
resolves DATA_DIR to that empty local copy; an ambient export of the absolute
path does not reliably override it, because `pipeline_loaders` calls
`load_dotenv()` on the worktree's own `.env`.

**The fix is `make data`**, not running in the primary checkout: it is
`dvc checkout` from the local cache — no network — and both
`.githooks/post-checkout` and the Makefile document it, having deliberately
stopped populating worktrees eagerly because copying ~1.7 GB timed out worktree
creation. Run it once in a fresh worktree that needs the corpus, then work
normally inside the worktree. (`make corpus-sync` also fetches from the padme
remote if the cache lacks a blob.)

Two consequences. Read a "clean rebuild produces [MISSING]" report
skeptically — an empty worktree `data/` reproduces that symptom with the
artifact present all along (ticket 0349). And never treat the empty `data/` as
a reason to run Phase 1 in the primary checkout: on 0347 that bypassed the
worktree's isolation and the DVC bookkeeping with it. See
[[feedback_corpus_rerun_byte_compare]].
