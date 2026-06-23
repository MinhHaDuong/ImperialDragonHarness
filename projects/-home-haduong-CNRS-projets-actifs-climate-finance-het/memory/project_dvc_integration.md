---
name: DVC integration (complete)
description: DVC set up for Phase 1 data versioning, pipeline DAG, machine sync, and reproducibility archives
type: project
---

DVC integration completed 2026-03-15. All tickets merged (#101–#104, #109, #113, #114, PRs #105–#108, #112, #115, #116).

**Architecture:**
- Data lives in `data/` inside the repo (symlinks to DVC cache)
- DVC cache EXTERNAL: `/home/haduong/data/projets/Oeconomia-Climate-finance/dvc-cache` (doudou), `/data/projets/dvc-cache/oeconomia` (padme). Set via `.dvc/config.local` (gitignored).
- `CLIMATE_FINANCE_DATA` env var REMOVED — scripts hardcode `data/` relative to BASE_DIR
- DVC remote: `padme:/data/projets/dvc/oeconomia-climate-finance/`
- On padme: local override `dvc remote modify --local padme url /data/projets/dvc/...`

**Source column normalized (1NF):**
- `source` = primary source (single value, highest priority)
- `from_openalex`, `from_semanticscholar`, `from_istex`, `from_bibcnrs`, `from_scispsace`, `from_grey`, `from_teaching` = boolean provenance columns
- `source_count` = sum(from_*), no more pipe-parsing
- `FROM_COLS` and `SOURCE_NAMES` constants in `utils.py`

**Teaching canon refactored:**
- `build_teaching_canon.py` extracts all readings directly (100 lines, was 363)
- Single merge in discover stage (was double)
- `teaching_canon.csv` and `teaching_gaps.csv` eliminated
- Protection uses `from_teaching == 1` instead of loading separate file

**Workflow:**
- `dvc push` / `dvc pull` syncs data between machines (bidirectional)
- `dvc repro` runs the pipeline (replaces `make corpus`)
- `dvc commit --force` snapshots current files without re-running pipeline
- `make archive-manuscript` / `make archive-datapaper` for reproducibility
- `make check-fast` for quick tests (excludes slow/network tests)

**Key decisions:**
- Per-project DVC store (not unified across projects)
- doudou = local machine name
- Fulltexts/PDFs stay outside DVC (bigger unification vision parked)
- `make citations` shortcut removed (wontfix #111) — use `dvc repro enrich`
