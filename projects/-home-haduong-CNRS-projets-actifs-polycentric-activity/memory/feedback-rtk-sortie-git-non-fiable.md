---
name: feedback-rtk-sortie-git-non-fiable
description: "Symptômes de pipe corrigés en rtk v0.45.0 (passthrough isatty), écart résiduel sur git log nu dont la cause n'est pas isolée — le test empirique tranche, pas la lecture du code amont"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-14T15:40:00.000Z
---

**L'observation.** Sous le hook rtk, `git log --oneline -5` et
`git log --oneline -1 main` ont rendu des SHAs et des messages cohérents entre
eux mais en désaccord avec l'état réel : `git rev-parse main` donnait `eb22f4f`
là où `git log` affichait `063eb77`, et la branche était en fait 4 commits en
retard sur `origin/main` (harness, 2026-08-14).

**La portée dépasse git** (roar HET, 2026-08-14). Trois occurrences dans une
seule session, dont deux hors git : `git log --oneline -4 origin/main` a affiché
l'historique d'un *autre* manuscrit alors que `merge-base --is-ancestor` disait
juste ; `wc -l < fichier` a rendu 0 sur un fichier de trois lignes ; et
`head -1 rows.jsonl | log-celebration` a livré du JSON corrompu au caractère 3,
avec un `JSONDecodeError` pour seul symptôme. Le défaut n'est donc pas « rtk
réécrit git », c'est « rtk réécrit toute sortie », et il fait le plus de dégâts
quand cette sortie alimente un autre programme au lieu d'un lecteur humain.

**Les trois symptômes ci-dessus sont corrigés en v0.45.0** (vérifié 2026-08-14,
après montée depuis 0.34.3), chacun recontrôlé contre `rtk proxy`. Le correctif
général est le passthrough isatty demandé en amont (rtk-ai/rtk #1282) : la
réécriture est sautée dès que la sortie n'est pas un terminal, donc `ls | cat`
rend du brut tandis qu'un `ls` nu reste compacté. Ce garde est **au-dessus** des
commandes individuelles — d'où l'absence de `IsTerminal` dans `read.rs`, qui
n'en a pas besoin. Conclure à l'absence de garde en grepant le fichier de
commande est une inférence fausse : un contributeur amont l'a faite puis
rétractée sur ce même ticket, et je l'ai refaite avant de tester. **Le test
empirique tranche, la lecture du code amont non.**

**L'écart résiduel sur `git log` nu reste ouvert, et sa cause a été inventée
deux fois.** La première version de cette entrée disait que la commande
« ment » et rendait des SHAs *absents* de l'état réel ; une correction ultérieure
disait l'inverse — sortie filtrée et non fabriquée, `git.rs` injectant
`--no-merges` par défaut. Aucune des deux n'est établie : re-sondé le
2026-08-14, l'écart ne s'est reproduit que lorsqu'un autre `git log` précédait
la commande dans le même appel, et a disparu quand elle tournait seule. Deux
demandes de fusion sœurs, chacune au vert, ont porté cette cause inventée, et
l'une a été fusionnée avant le recoupement. C'est le défaut que nomme
`rules/workflow.md` § Diagnosis discipline : rapporter l'observation, retenir la
cause tant qu'elle n'est pas isolée.

**Pourquoi l'isolement demande un vrai terminal.** Par la règle de passthrough
ci-dessus, capturer la sortie par un tube ou une redirection désarme la
réécriture — et sous un harnais d'agent, toute sortie de commande est capturée.
Une sonde lancée depuis une session d'agent rendra donc « aucun écart » que le
défaut soit là ou non : le « rien trouvé » indistinguable du « je n'ai pas su
regarder ». C'est la même forme de piège que le reste de cette entrée décrit,
appliquée à sa propre vérification.

**Why:** une sortie qui *paraît* valide est pire qu'un no-op. Un branchement
décidé sur ces SHAs part d'une base fausse sans aucun signal d'erreur — et cela
reste vrai quel que soit le mécanisme, ce qui est précisément la raison de
garder la règle sans attendre le diagnostic.

**How to apply — vérifier par effet, jamais en analysant une sortie.** Pour tout
état git qui conditionne une décision (branchement, merge, currency), utiliser la
plomberie — `git rev-parse`, `git rev-list --count A..B`, `git merge-base
--is-ancestor` en code de retour — ou forcer la sortie brute avec `rtk proxy git
...`. Ne jamais lire un SHA, un compte ou une pointe depuis un `git log`
porcelain passé par le hook. Hors git, il n'y a plus de contournement de pipe à
maintenir depuis v0.45.0 ; ce qui reste, c'est de vérifier `rtk --version` dès
qu'une sortie paraît fausse, et de garder `rtk proxy` comme témoin qui décide si
un résultat suspect vient de rtk ou du réel. Un `JSONDecodeError` inexpliqué au
milieu d'un pipeline reste la signature du défaut sur une version ancienne. Même
logique que [[feedback-merge-verifier-le-diff-pas-la-sortie]] : c'est l'état
vérifié qui fait foi, pas le message affiché.
