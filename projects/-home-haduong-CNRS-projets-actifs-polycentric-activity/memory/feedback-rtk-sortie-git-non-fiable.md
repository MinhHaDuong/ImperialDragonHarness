---
name: feedback-rtk-sortie-git-non-fiable
description: "sous rtk, une sortie lue peut désaccorder l'état réel (git log contre rev-parse, wc à 0, JSON tronqué) — vérifier par effet, jamais en analysant une sortie ; cause non isolée"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-14T12:05:46.304Z
---

**L'observation, sans le diagnostic.** Sous le hook rtk, `git log --oneline -5`
et `git log --oneline -1 main` ont rendu des SHAs et des messages cohérents
entre eux mais en désaccord avec l'état réel : `git rev-parse main` donnait
`eb22f4f` là où `git log` affichait `063eb77`, et la branche était en fait
4 commits en retard sur `origin/main` (harness, 2026-08-14).

**La cause n'est pas établie, et deux tentatives l'ont inventée.** La première
version de cette entrée disait que la commande « ment » et rendait des SHAs
*absents* de l'état réel. La correction qui a suivi disait l'inverse — sortie
filtrée et non fabriquée, `git.rs` injectant `--no-merges` par défaut. Aucune
des deux ne tient : re-sondé le 2026-08-14, l'écart ne s'est reproduit que
lorsqu'un autre `git log` précédait la commande dans le même appel, et a disparu
quand elle tournait seule. Deux demandes de fusion sœurs, chacune au vert, ont
porté cette cause inventée. C'est le défaut que nomme `rules/workflow.md`
§ Diagnosis discipline : rapporter l'observation, retenir la cause tant qu'elle
n'est pas isolée. Elle a reçu un nom trois heures trop tôt, et le nom était
inventé — deux fois.

**Pourquoi l'isolement demande un vrai terminal.** Capturer la sortie par un
tube ou une redirection désarme la réécriture ; sous un harnais d'agent, toute
sortie de commande est capturée. Une sonde lancée depuis une session d'agent
rendra donc « aucun écart » que le défaut soit là ou non — le « rien trouvé »
indistinguable du « je n'ai pas su regarder ».

**Why:** une sortie qui *paraît* valide est pire qu'un no-op. Un branchement
décidé sur ces SHAs part d'une base fausse sans aucun signal d'erreur — et cela
reste vrai quel que soit le mécanisme, ce qui est précisément la raison de garder
la règle sans attendre le diagnostic.

**La portée dépasse git** (roar HET, 2026-08-14). Trois occurrences dans une
seule session, dont deux hors git : `git log --oneline -4 origin/main` a affiché
l'historique d'un *autre* manuscrit alors que `merge-base --is-ancestor` disait
juste ; `wc -l < fichier` a rendu 0 sur un fichier de trois lignes ; et
`head -1 rows.jsonl | log-celebration` a livré du JSON corrompu au caractère 3,
avec un `JSONDecodeError` pour seul symptôme. Le défaut n'est donc pas « rtk
réécrit git », c'est « rtk réécrit toute sortie », et il fait le plus de dégâts
quand cette sortie alimente un autre programme au lieu d'un lecteur humain.

**How to apply — vérifier par effet, jamais en analysant une sortie.** Pour tout
état git qui conditionne une décision (branchement, merge, currency), utiliser la
plomberie — `git rev-parse`, `git rev-list --count A..B`, `git merge-base
--is-ancestor` en code de retour — ou forcer la sortie brute avec `rtk proxy git
...`. Ne jamais lire un SHA, un compte ou une pointe depuis un `git log`
porcelain passé par le hook. Hors git : ne pas construire un pipeline
`producteur | consommateur` sur du texte structuré (JSON, TSV) ; écrire dans un
fichier et faire lire le fichier par le consommateur, ou passer la valeur en
littéral. Un `JSONDecodeError` inexpliqué au milieu d'un pipeline est la
signature. Même logique que
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : c'est l'état vérifié qui
fait foi, pas le message affiché.
