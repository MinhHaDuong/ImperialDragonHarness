---
name: project-preprint-target-main-md
description: "The arXiv preprint WP is slides/manuscript/main.md — report.tex is an internal working document with \"no future\" (author, 2026-06-05)"
metadata: 
  node_type: memory
  type: project
  originSessionId: dd5fd1a6-54f6-4a9c-8dac-81a5fb68b497
---

The author redefined the publication target on 2026-06-05: **`slides/manuscript/main.md` IS the arXiv preprint** (ticket 0435, "nothing new, no restructure"); `report/report.tex` is an internal working document — "Je vois pas trop d'avenir à report.tex". Keep report.tex coherent (it shares the generated-artifact DAG) but spend editorial effort on main.md. Consequence: tickets 0255–0262 (Exp2 sections for report.tex) are probably moot — arbitrate before executing. The annex (recognition matrix + status table) was ported to main.md as Annex E with Figure 7 (PR #767); Annex D is Temporality. main.pdf is gitignored (pandoc+citeproc build, `make manuscript/main.pdf` from slides/).
