---
name: gide-slides
description: "Deck de présentation pour le colloque Charles Gide (Vannes, juillet 2026) — emplacement, build, état"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3a2802ee-f462-4671-a81e-3f0791af6741
---

Présentation pour le 21e colloque Charles Gide, Vannes, 2–4 juillet 2026
(« Économistes sous contrainte », d'après `manuscript-Gide.qmd`).

- Source : `climate-finance-het/content/slides-gide.qmd` (Beamer/metropolis, fr, ~31 pages dont overlays).
- Build : `quarto render content/slides-gide.qmd --to beamer` **depuis le checkout principal**
  (un worktree frais échoue au scan projet : tables gitignorées absentes). PDF copié dans
  le dossier mission Vannes : `slides-Gide.pdf`.
- Assets : `content/slides-assets/` — 2 photos CC versionnées (COP29, ligne 380 kV) + logo CIRED +
  bandeau tutelles ; portrait Corfee-Morlot + couvertures OCDE/Oxfam **gitignorés** (©, à recopier
  depuis le checkout principal pour builder dans un worktree). `CREDITS.md` documente tout.
- Figures : voir [[cfhet-handoff-figures]]. La figure thèmes a une variante `fig_composition_wide.png`
  (option `--wide` de `plot_fig2_composition.py` : 2×3 paysage, titres coupés au « & », sans sous-titres).
- État : relu par panel de 4 reviewers (PR #848–857 mergées). Restent volontairement non traités :
  hedge constructiviste slide 5 (assumé en Q&A), « économie des conventions » comme tradition (=
  révision papier, pas faite). Le talk ne doit pas devancer le papier.
