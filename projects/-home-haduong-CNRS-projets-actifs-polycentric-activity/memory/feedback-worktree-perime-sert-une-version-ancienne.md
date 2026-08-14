---
name: feedback-worktree-perime-sert-une-version-ancienne
description: "Un worktree d'une autre session peut être en retard — y lire un fichier pour connaître « l'état courant » sert une version périmée sans le dire"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 81befdb7-37e9-46db-8115-1200addcda78
  modified: 2026-08-14T09:38:29.794Z
---

Pour établir l'état courant d'un fichier, lire `origin/main` ou le checkout
principal — jamais le worktree d'une autre session sans dater ce qu'on y
trouve. Un worktree vivant peut avoir plusieurs jours de retard, et rien dans
le fichier ne le signale.

**Why:** 2026-08-14, l'auteur annonce « on a changé le titre ». `origin/main`
et le checkout principal portaient « Eight Discoveries, No Eponym » ; j'ai
cherché ailleurs, trouvé « An Extreme Multiple: Eight **Independent**
Discoveries » dans le worktree `het-round3-structure`, et conclu que c'était
le nouveau. C'était l'ancien : le commit `ed06e55` « pivoter le titre sur
l'éponyme » avait fait le remplacement, et ce worktree était simplement en
retard. J'ai écrit dans un ticket tout un développement sur l'enjeu que le
mot *Independent* faisait peser — exactement à l'envers, puisque le pivot
l'avait au contraire retiré du titre. Correction faite par l'auteur, ticket
et PR à réécrire.

**How to apply:** le sens d'un changement se date avec `git log -S "<chaîne>"`,
qui montre quel commit l'introduit et lequel le retire — un seul commit y
apparaissant pour les deux chaînes prouve le remplacement et son sens. Deux
minutes, et cela aurait évité l'inversion. Quand un fichier trouvé hors du
checkout principal contredit celui-ci, l'hypothèse par défaut est qu'il est
**en retard**, pas en avance. Voir [[feedback-grep-context-audit]] : trouver
une occurrence ne dit pas ce qu'elle vaut.
