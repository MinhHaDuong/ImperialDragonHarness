---
name: prose-vs-code-workflow
description: "Discipline différenciée par workpackage — code en worktree+PR, prose éditée en place dans le checkout de l'auteur"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1848c079-892d-4cc3-aff1-bf176e1c7e39
---

Dans les dépôts de papiers multi-manuscrits (ex. polycentric_activity), Minh
veut une discipline différenciée : code/données = machinerie complète
(worktree, branche, PR, /gaze) ; prose de manuscrit = édition en place dans
son checkout, commits au fil de l'eau sur main ou branche de papier, relecture
par PDF recompilé et latexdiff entre tags — jamais de worktree jetable pour la
prose interactive.

**Why:** L'isolation worktree le coupe du texte : un manuscrit se co-édite en
allers-retours courts (précédent : le workflow ODT annoté avec Pierre
Matarasso sur le papier Œconomia). Le diff de PR n'est pas son interface de
relecture pour la prose.

**How to apply:** En session interactive sur de la prose, ne pas isoler —
éditer dans le checkout. Les passes autonomes sur la prose produisent des
rapports (panels de référés, registres de sources → conception/), jamais
d'édits directs du manuscrit ; ce qui modifie le manuscrit passe soit par la
session interactive, soit par branche+PR que l'auteur arbitre — jamais les
deux modes en même temps sur le même fichier. Protection anti-collision par
séparation des lanes (tickets autonomes → analysis/, conception/, refs.bib),
pas par isolation git. Règle codifiée dans le harnais IDH : rules/git.md
§ Prose vs code workpackages (PR de 2026-07-06). Voir aussi
[[plain-directory-names]].
