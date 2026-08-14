---
name: feedback-rejouer-ou-reconstruire-une-branche
description: "Quand deux commits d'une branche s'annulent, reconstruire l'état final sur origin/main coûte moins cher que rejouer leur histoire"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d656551a-8f4e-4a1d-b7f0-2ea8536cf852
  modified: 2026-08-14T08:30:41.570Z
---

Quand une branche contient des commits qui s'annulent entre eux (un ajout puis
son retrait, une correction puis sa révocation), ne pas les rejouer contre une
base qui a bougé. Remettre la branche sur `origin/main` et réappliquer le seul
**état final** en un commit.

**Why :** rejouer une histoire dont des morceaux se neutralisent fait résoudre
des conflits sur du contenu qui ne survivra pas au dernier commit — chaque
conflit résolu est du travail jeté d'avance. Une session parallèle a rejoué
quatre commits dont deux s'annulaient contre une base mouvante et a enchaîné
conflit sur conflit ; elle a abandonné, repris `origin/main` et réappliqué
l'état final, obtenant un commit propre au lieu de quatre (polycentric_activity,
MR #100, 2026-08-14). L'histoire d'une branche de travail n'a pas de valeur
propre : ce qui compte est l'état qu'elle livre et la justification qu'elle
porte, et les deux tiennent dans un commit.

**How to apply :** avant un rebase pénible, regarder si des commits de la
branche se neutralisent (`git log -p` ou un simple `git diff origin/main`
comparé à la somme des commits). Si oui : `git switch -c <branche>-v2
origin/main`, réappliquer l'état final, rédiger un message qui porte la
justification complète, vérifier avec
[[feedback-merge-verifier-le-diff-pas-la-sortie]] que le diff ne montre que vos
fichiers. Ne s'applique pas à une branche dont les commits sont des étapes
indépendantes et lisibles — là, l'histoire vaut d'être gardée.
