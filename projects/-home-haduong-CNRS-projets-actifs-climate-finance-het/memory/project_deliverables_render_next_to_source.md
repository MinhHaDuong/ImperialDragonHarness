---
name: project_deliverables_render_next_to_source
description: The deliverables/ reorg — each paper/deck is a self-contained deliverables/<x>/ Quarto project; PDFs render next-to-source; top-level output/ is gone
metadata: 
  node_type: memory
  type: project
  originSessionId: 2317022c-d609-4ac0-b6fa-8e23969f5f97
---

**Landed 2026-07-10, raid 237, PRs #1002 (ticket 0226) + #1003 (ticket 0237).**
The build+prose children of tracker 0223 (which is the code+prose axis of the
0221 repo-layout reorg). Tracker 0223 stays OPEN — the code workstream 0225 is
still open.

## New layout
- Each deliverable is its own Quarto project under `deliverables/<x>/` with its
  own `_quarto.yml` (no more `content/` mega-project + `_quarto-manuscript*.yml`
  exclusion masks — those are deleted). 11 docs across 9 folders: `manuscript/`
  (manuscript.qmd + manuscript-Gide.qmd + manuscript.mk), `data-paper/`,
  `corpus-report/`, `technical-report/`, `multilayer/` (multilayer-detection +
  -techrep), `agentic/`, `zoo/`, `slides-gide/`, `slides-eshet/`.
- Shared assets in `deliverables/_shared/` (`bibliography/`, `_includes/`,
  generated `figures/` + `tables/`, `technical-report-vars.yml`); referenced by
  `../_shared/...`. Includes resolve relative to the TOP rendering doc, and every
  folder sits one level under `deliverables/`, so the prefix is uniform.

## Render lands next-to-source; output/ is retired
- **Quarto single-file `quarto render <file>.qmd` ignores the project
  `output-dir`** — it writes the PDF/DOCX beside the source. So each render target
  is `deliverables/<x>/<doc>.<pdf|docx>` (gitignored), the Make target EQUALS the
  actual output (Make now verifies it — the old `output/content/*.pdf` targets and
  the whole top-level `output/` dir are gone). Release is out-of-project (copies
  into `papiers/<state>/<track>/` / archive tarballs), so it doesn't need `output/`.
  See [[feedback_render_bitcompare_is_the_gate]] for the two defects this caught.

## Build split by phase (0237)
- Each deliverable owns a Phase-3 render `.mk` (render-only). Concern `.mk`
  (`divergence.mk`, `zoo.mk`, `multilayer-detection.mk`, `venues.mk`,
  `separation.mk`) are pure Phase-2 — 0 render rules. `paths.mk` is the shared
  var interface `-include`d by both sides.
- `make papers`/`manuscript` are **phony recursive `$(MAKE) -f deliverables/<x>/<x>.mk`**
  recipes, NOT `-include` — a plain include would let the root Makefile's
  `$(REFINED)`-dependent inline figure recipes trigger Phase-2. `make papers` is
  now corpus-free (no `check-corpus`, no `uv run`); the contract is "run
  `make analysis`, then render." Guard: `test_build_phase_separation.py`'s
  `test_no_mk_file_mixes_render_and_compute` (adherence, classifies by recipe).
- `multilayer-detection.mk`'s Phase-2 remainder stays at root (feeds two
  deliverables → analysis concern, not deliverable-scoped); rename to
  `scripts/analysis/` deferred to 0225.

## Consequences to remember
- **A future cherry-pick onto `submission/oeconomia-varia`** (frozen at old
  `content/` paths) needs path remapping — main and the submission branch diverge
  on file location from #1002 forward. See [[project_frozen_manuscript_vs_live_companions]].
- Companions `technical-report`, `multilayer*`, `zoo` need `make analysis`
  (zoo/companion figures: `schematic_*.png`, `fig_zoo_*.png`, `fig_companion_*.png`)
  before they render — those figures are NOT git-tracked and were absent in the
  checkout, so they could not be byte-validated during the raid (manuscript,
  corpus-report, data-paper WERE, all byte-identical old-vs-new).
- `architecture.md` § Project structure + § Artifact homes were updated to match.
