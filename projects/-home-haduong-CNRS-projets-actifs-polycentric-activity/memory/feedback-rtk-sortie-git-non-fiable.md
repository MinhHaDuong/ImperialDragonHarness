---
name: feedback-rtk-sortie-git-non-fiable
description: "rtk réécrit la sortie de git log et peut renvoyer des SHAs plausibles mais faux ; lire l'état avec la plomberie ou rtk proxy"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-14T12:03:43.863Z
---

Le hook rtk réécrit la sortie des commandes git. Sur `git log --oneline -5` et
`git log --oneline -1 main`, il a renvoyé des SHAs et des messages cohérents
entre eux mais absents de l'état réel : `git rev-parse main` donnait `eb22f4f`
là où `git log` affichait `063eb77`, et la branche était en fait 4 commits en
retard sur `origin/main` (harness, 2026-08-14).

**Why:** une sortie réécrite qui *paraît* valide est pire qu'un no-op.
`rules/git.md` note déjà que `git branch -vv | awk '/: gone]/'` se tait sous
rtk ; ici la commande ne se tait pas, elle ment. Un branchement décidé sur ces
SHAs part d'une base fausse sans aucun signal d'erreur.

**How to apply:** pour tout état git qui conditionne une décision (branchement,
merge, currency), utiliser la plomberie — `git rev-parse`, `git rev-list --count
A..B`, `git merge-base --is-ancestor` en code de retour — ou forcer la sortie
brute avec `rtk proxy git ...`. Ne jamais lire un SHA depuis un `git log`
porcelain passé par le hook. Même logique que
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : c'est l'état vérifié qui
fait foi, pas le message affiché.
