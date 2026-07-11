---
name: cfhet-handoff-figures
description: climate-finance-het — which figure files the writing phase consumes vs gitignored pipeline outputs
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3a2802ee-f462-4671-a81e-3f0791af6741
---

Dans `climate-finance-het`, `.gitignore` exclut `content/figures/*`, mais trois
figures sont force-versionnées car consommées par la phase rédaction
(`manuscript-Gide.qmd`, slides) :

- **`fig_bars_v1.png`** — Figure 1 (croissance de la littérature)
- **`fig_breaks.png`** — Figure 2 (vitesse de renouvellement / ruptures)
- **`fig_composition.png`** — Figure 3 (recomposition thématique)

Les variantes **non suffixées** `fig_bars.png` et `fig_breakpoints.png` sont des
sorties brutes du pipeline calcul, **gitignorées** → absentes d'un worktree frais.
Pour tout livrable rédaction (slides, manuscrit), référencer les fichiers versionnés
ci-dessus, jamais les variantes brutes.

Conséquence build : un worktree frais ne peut pas faire `quarto render` du projet
entier (des includes de tables gitignorées, p.ex. `tables/tab_corpus_sources.md`,
manquent). Rendre les slides en isolation (copie autonome du `.qmd` + les 3 figures
versionnées + `slides-assets/`, sans `_quarto.yml`), ou builder depuis le checkout
principal où tout est généré. Slides Gide : `content/slides-gide.qmd`.
