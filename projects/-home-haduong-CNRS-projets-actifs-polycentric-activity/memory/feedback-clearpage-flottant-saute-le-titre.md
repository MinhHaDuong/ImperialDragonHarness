---
name: feedback-clearpage-flottant-saute-le-titre
description: "Un \clearpage forcé devant un \section fait sauter un flottant [t] voisin au-dessus du titre — \FloatBarrier (placeins) corrige ; découvert en construisant, pas en relisant"
metadata:
  type: feedback
---

Insérer un `\clearpage` juste avant un `\section{...}` pour garantir que la
section démarre en haut d'une page fraîche crée un piège si un flottant
`[t]`-seul (table ou figure) est défini quelques paragraphes plus loin, sur
la même page : LaTeX extrait les flottants du flux normal et les place au
top de la page où ils atterrissent, **indépendamment de l'ordre textuel** —
le flottant peut donc apparaître au-dessus du titre de section qui le
précède pourtant dans la source. Ce n'est pas un bug de LaTeX, c'est son
comportement normal ; le piège est que `\clearpage` + titre en tout haut de
page crée précisément la configuration où ce comportement devient visible et
gênant, alors qu'il ne l'était pas avant l'ajout du saut de page forcé.

**Why:** repéré en construisant la variante HAL de `article-het/manuscrit.tex`
(ticket 0281, 2026-08-18) — le tableau du *money pump* (`\begin{table}[t]`,
défini deux paragraphes après `\section{Introduction}`) sautait au-dessus du
titre dès qu'un `\clearpage` scripté forçait l'introduction en haut d'une
page fraîche. Absent du PDF canonique (où l'introduction ne tombe jamais en
haut de page), donc invisible tant que personne ne force ce point de rupture
— un rendu « clean » (0 avertissement `check_tex_unresolved.py`) ne l'aurait
jamais signalé : seule la lecture du PDF rendu (`pdftotext -f N -l N`,
page par page) l'a montré. Cas d'école de « assert the product, not the exit
code » (`rules/manuscript-build.md`).

**How to apply:** avant d'insérer un `\clearpage` (ou tout saut de page forcé)
juste avant un titre de section, vérifier si un flottant `[t]`-seul est
défini dans les paragraphes qui suivent immédiatement ce titre. Si oui,
charger `\usepackage{placeins}` et insérer `\FloatBarrier` juste après le
titre — le flottant ne peut plus remonter avant la barrière, donc plus
au-dessus du titre. Toujours vérifier sur le PDF rendu (pas seulement sur la
compilation propre) que l'ordre de lecture tient : `pdftotext -f <page> -l
<page> -layout`, une page à la fois, autour de chaque saut de page forcé
nouvellement introduit.

Contexte plus large : le script `article-het/releases/hal_variant.py`
implémente pour la première fois dans ce dépôt le patron « Variants are
transform layers » de `rules/pdf-finishing.md` (jusque-là documenté
uniquement par référence à climate-finance-het) — transformation de chaînes
sur `manuscrit.tex`, rendu, puis `git checkout --` pour annuler. Réutilisable
tel quel si MIMO ou no-arbitrage veulent un jour leur propre frontispice de
preprint sans le faire porter par le fichier soumis à la revue.
