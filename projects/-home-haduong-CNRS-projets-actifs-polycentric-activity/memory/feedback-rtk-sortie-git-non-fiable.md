---
name: feedback-rtk-sortie-git-non-fiable
description: "rtk réécrit encore un `git log` nu — injection --no-merges toujours active en v0.45.0 ; le garde est la forme de sortie écrite dans la commande, donc capturer la sortie désarme ce qu'on mesure"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
---

**Toujours actif en v0.45.0, vérifié le 2026-08-14.** `git log` nu, sans drapeau
de limite, perd tous ses commits de merge. Sur la plage `eb22f4f..origin/main` :
la commande nue rend 14 lignes, `rtk proxy` la même commande en rend 22, et les
8 manquantes sont exactement les 8 merges. Les sujets longs sont aussi tronqués
par `…`. Ce n'est pas de l'histoire ancienne : c'est le comportement du jour.

**Mécanisme :** `git.rs` injecte `--no-merges` quand aucun drapeau de limite
n'est présent (`if !wants_merges && !has_limit_flag`). Les merges tombent, des
commits plus anciens remontent pour honorer le compte. La sortie est **filtrée,
non fabriquée** : chaque SHA affiché existe, aucun n'est forcément le sommet.
`git log --oneline --no-merges -3 eb22f4f` rejoue exactement les trois SHAs
observés le matin même, quand `rev-parse main` disait `eb22f4f` et le porcelain
`063eb77`.

**Le garde est la forme de sortie écrite dans la commande**, pas un test isatty
à l'exécution. Mesuré : `ls` nu rend le format rtk (slashs, tailles, dotfiles),
`rtk proxy ls` rend du brut, `ls | cat` et `ls > f` rendent du brut — et
`[ -t 1 ]` est faux dans les quatre cas, donc un test runtime ne peut pas être
ce qui déclenche. Tube ou redirection dans le texte de la commande ⇒ pas de
réécriture ; commande nue ⇒ réécriture, y compris depuis une session d'agent
dont la sortie n'est jamais un terminal.

**Le piège de mesure, qui est le vrai coût.** `$(…)`, un tube ou une
redirection désarment la réécriture : la façon évidente de capturer une sortie
pour la comparer est précisément celle qui éteint ce qu'on veut mesurer, et
rend un satisfecit gratuit. J'ai conclu deux fois de suite à tort sur cette
base — d'abord « l'injection a disparu », puis « depuis un agent la réécriture
ne peut être ni observée ni disculpée ». Les deux étaient des artefacts de
sonde. **La sonde qui marche est une commande nue comparée à `rtk proxy`.**

**Ce que v0.45.0 a corrigé** (rtk-ai/rtk #1282, « piped or redirected ») : le
passthrough tube/redirection, et l'exemption quand un drapeau de limite est
présent — d'où `git log --oneline -5`, lossy en 0.34.3, correct aujourd'hui.
Le garde est **au-dessus** des commandes individuelles, d'où l'absence de
`IsTerminal` dans `read.rs` : conclure à son absence en grepant le fichier de
commande est une inférence fausse, faite puis rétractée par un contributeur
amont sur ce même ticket.

**Symptômes hors git observés le 2026-08-14, sans mécanisme établi :**
`wc -l < fichier` rendant 0 sur trois lignes ; `head -1 rows.jsonl | consommateur`
livrant du JSON corrompu au caractère 3 ; un `make -j4 --output-sync=target |
grep -c` comptant 2 là où 3 était juste, avec `make: Entering directory` sorti
*après* le corps de la recette. Une déduplication de lignes adjacentes explique
mieux ce dernier qu'une troncature — lignes perdues identiques, une seule
manquante et non une queue, réordonnancement qu'une troncature ne produit pas —
mais cela reste une hypothèse. Tous passaient par un tube, donc sous v0.45.0 ils
ne seraient plus réécrits du tout ; aucune cause n'est établie et il ne faut
leur en prêter aucune.

**How to apply:** ne jamais lire un SHA dans un `git log` nu — il perd les
merges, donc le sommet. Pour l'état qui conditionne une décision, plomberie et
codes de retour : `git rev-parse`, `git rev-list --count A..B`,
`git merge-base --is-ancestor`. Pour inspecter, `rtk proxy git log …` ou un
drapeau de limite. Pour tester rtk lui-même, commande nue contre `rtk proxy`,
jamais une capture. Et la règle qui survit à toute version, parce qu'elle ne
dépend d'aucune sortie : **vérifier par effet.** Un compteur de garde se règle
en injectant une citation fantôme dans les trois manuscrits et en observant les
trois compilations échouer et les trois PDF disparaître — verdict insensible à
ce que le proxy fait de stdout. Même famille que
[[feedback-controle-cadence-glob-etroit]] et
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : un contrôle dont le « rien
à signaler » est indiscernable du « je n'ai pas pu regarder » n'est pas un
contrôle.
