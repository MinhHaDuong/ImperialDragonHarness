---
name: cired-digital-messh26-slides
description: "MeSSH26 talk slides for Cirdi — location, build, and accepted-abstract positioning"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3d4e980c-b6ec-47d6-ad5d-05af856ce8bf
---

Talk deck for **MeSSH26** (Méthodes pour les SHS, Aubervilliers, 9–10 July 2026),
panel **"Fouille de texte"** (Thu 17h15–18h45, discussant Katja Ploog). 20 min + live demo.

- **Accepted abstract / title**: *« De la recherche par mots-clés à la synthèse sémantique — retour d'expérience sur un dispositif RAG en SHS »* (in `~/CNRS/missions/actif/2026-07-09 MeSSH Campus Condorcet/program_messh_long.pdf`).
- **Take-home** (deliberately nuanced, not imperative): HAL gives *lexical* access; *« Et si HAL offrait aussi l'accès sémantique ? »* — with governance/liability/scale named as open obstacles.
- **Location**: `cired.digital` repo → `slides/slides-messh.qmd` (+ `slides/slides-assets/`), tracked. Rendered PDF + keep-tex are gitignored (`slides/.gitignore`).
- **Build**: `make slides` → `quarto render slides-messh.qmd --to beamer` (metropolis, xelatex). Writing-side clean-room: consumes committed figures only, no data/uv. `--to beamer` is required (`--to pdf` renders a plain article, not beamer).
- **Toolchain choice**: Quarto→Beamer mirrors the GIDE deck in `climate-finance-het` and the Quarto report `reports/rapport_usages_quarto_python.qmd`; figures cropped/downscaled from `~/CNRS/papiers/sent/CIRED.digital final report/fig/` for slide legibility (500 KB pre-commit large-file limit applies).
- **Technical facts stated** (verified against code): engine = **R2R** (`r2r-api.cired.digital`), chunking by length, retrieval hybrid (`use_hybrid_search: true` = dense + BM25). ~1199 publications indexed. Costs measured: 1.71 M Mistral tokens = €0.32 (prod), ~25 M OpenAI tokens (dev).
- Shipped over PRs #274 (v1+v2) and #275 (v3, post 4-reviewer panel). See [[cired-digital-merge-and-tracker]] for the rebase-only merge flow.
