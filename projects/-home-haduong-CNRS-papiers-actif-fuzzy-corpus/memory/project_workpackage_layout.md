---
name: Project — two-workpackage layout (paper + analysis)
description: Paper sources are in paper/, analysis pipeline at repo root; handoffs are figures/ and output/tables/
type: project
originSessionId: 791ae788-5308-4716-b2da-e0639978e7a9
---
After ticket 0040 (PR #40, merged 2026-04-23), the repo has a two-workpackage layout:

- **Writing WP:** `paper/main.tex`, `paper/refs.bib`, `paper/sections/*.tex` — built by `paper.mk` using `tectonic -Z search-path=. paper/main.tex` from repo root. Needs only TeX Live; no Python.
- **Analysis WP:** `scripts/`, `src/fuzzy_corpus/`, `Makefile` — produces handoff artifacts.
- **Handoffs (committed):** `figures/*.pdf` and `output/tables/*.tex` — written by analysis, consumed by paper via tectonic's cross-directory search.

**Why:** `tectonic -Z search-path=.` (run from repo root) covers `\input`, `\includegraphics`, and `\addbibresource` lookups across the `paper/` boundary without editing tex sources. Verified against tectonic PR #814 and issue #933.

**All 9 sections** are wired into `paper/main.tex` (PR #41, #44). Anchored kernel tables 1–3 and Figure 1 are stubs pending sample-tier script runs on padme. Run scripts with `--data-dir "/home/haduong/CNRS/papiers/actif/Oeconomia - Climate finance/data"` — Climate Finance data is available locally at that path.

**How to apply:** When editing or referencing paper sources, look in `paper/` not at repo root. When building, use `make -f paper.mk` or just `make`.
