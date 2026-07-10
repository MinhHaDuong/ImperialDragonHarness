---
name: project_writing_build_phase_separation
description: Writing workpackages build clean-room from git-tracked handoff artifacts; manuscript.mk is the template (0131/0163)
metadata: 
  node_type: memory
  type: project
  originSessionId: f849de87-bf31-4f36-8b5a-95ec3296ace4
---

The manuscript PDF now builds **clean-room** — no corpus data, no `uv`, no
`dvc`. Pattern landed 2026-06-28 (PR #833, ticket 0131 manuscript slice):

- **Handoff artifacts are git-tracked, like `content/_includes/` always was.**
  `.gitignore` uses ignore-then-negate: `content/figures/*` + `content/tables/*`
  ignored, but the manuscript's writing-facing deliverables are negated and
  committed — the 3 PNGs (`fig_bars_v1`, `fig_composition`, `fig_breaks`) and
  `tab_venues.md`. They are byte-stable (`save_figure` strips metadata), so no
  churn. Bulk analysis intermediates (`tab_lexical_tfidf.csv` 35 MB, etc.) stay
  ignored.
- **`manuscript.mk`** (root, sibling of `divergence.mk`) holds the
  `output/content/manuscript.{pdf,docx}` render rules, moved OUT of the main
  `Makefile` (which now `-include`s it). Prereqs = prose + committed deliverables
  ONLY — no `$(REFINED)`, no `$(MANUSCRIPT_FIGS)` data-built path. The Phase-2
  figure-from-data rules stay in the main Makefile.
- **Quarto project isolation gotcha:** a bare `quarto render content/manuscript.qmd`
  is NOT standalone — Quarto walks every doc in `_quarto.yml`'s render list during
  project discovery and fails on sibling papers' includes. Fix: a `manuscript`
  Quarto profile (`_quarto-manuscript.yml`) excluding sibling docs, set per-target
  via `export QUARTO_PROFILE := manuscript` in `manuscript.mk` so it doesn't leak
  into `make papers`.
- **Verify clean-room:** `make -f manuscript.mk -Bn output/content/manuscript.pdf`
  → recipe must be `quarto render …` only, zero `uv`/`python`/`refined`/`data` token.
  Guarded by `tests/test_build_phase_separation.py`.

The other papers (data-paper, technical-report, companion, multilayer, zoo) are
NOT yet migrated — their render rules stay data-coupled and their figures/tables
stay gitignored. Child ticket **0163** tracks the rollout (per-paper `.mk` +
profile, deliverable tracking, eviction of large intermediates). Tracker **0131**
stays open until 0163 closes. This is the harness rule "a writing-side build must
produce the manuscript from handoff artifacts alone" (see
[[feedback_decide_dont_micromanage]] — this defect surfaced because I hacked
around it twice before recognising the existing ticket).
