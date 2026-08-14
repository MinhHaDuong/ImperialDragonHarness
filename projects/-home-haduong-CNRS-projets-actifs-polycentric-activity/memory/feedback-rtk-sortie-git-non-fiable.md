---
name: feedback-rtk-sortie-git-non-fiable
description: "rtk réécrit la sortie des commandes ; git log rend des SHAs faux, et un texte piped vers un consommateur arrive corrompu — plomberie, codes de retour ou rtk proxy"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-14T12:05:46.304Z
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

**La portée dépasse git** (roar HET, 2026-08-14). Trois occurrences dans une
seule session, dont deux hors git : `git log --oneline -4 origin/main` a affiché
l'historique d'un *autre* manuscrit alors que `merge-base --is-ancestor` disait
juste ; `wc -l < fichier` a rendu 0 sur un fichier de trois lignes ; et
`head -1 rows.jsonl | log-celebration` a livré du JSON corrompu au caractère 3,
avec un `JSONDecodeError` pour seul symptôme. Le défaut n'est donc pas « rtk
réécrit git », c'est « rtk réécrit toute sortie », et il fait le plus de dégâts
quand cette sortie alimente un autre programme au lieu d'un lecteur humain.

**How to apply:** pour tout état git qui conditionne une décision (branchement,
merge, currency), utiliser la plomberie — `git rev-parse`, `git rev-list --count
A..B`, `git merge-base --is-ancestor` en code de retour — ou forcer la sortie
brute avec `rtk proxy git ...`. Ne jamais lire un SHA depuis un `git log`
porcelain passé par le hook. Hors git : ne pas construire un pipeline
`producteur | consommateur` sur du texte structuré (JSON, TSV) ; écrire dans un
fichier et faire lire le fichier par le consommateur, ou passer la valeur en
littéral. Un `JSONDecodeError` inexpliqué au milieu d'un pipeline est la
signature. Même logique que
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : c'est l'état vérifié qui
fait foi, pas le message affiché.
