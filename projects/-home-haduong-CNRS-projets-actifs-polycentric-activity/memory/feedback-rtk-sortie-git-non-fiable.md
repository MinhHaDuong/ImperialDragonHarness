---
name: feedback-rtk-sortie-git-non-fiable
description: "Sous 0.34.3 la sortie git était filtrée sans le dire (--no-merges), non fabriquée ; v0.45.0 saute la réécriture hors terminal, donc un agent ne peut plus ni l'observer ni la disculper — vérifier par effet"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
---

Le hook rtk réécrit la sortie des commandes — en 0.34.3, y compris quand elle
part dans un tube. Sur `git log --oneline -5` et
`git log --oneline -1 main`, la première ligne ne correspondait pas à
`git rev-parse main` : la plomberie donnait `eb22f4f`, le porcelain `063eb77`,
et la branche était en fait 4 commits en retard sur `origin/main` (harness,
2026-08-14).

**Mécanisme, établi après coup :** `git.rs` injectait `--no-merges` par défaut.
Les commits de merge tombaient et des commits plus anciens remontaient pour
honorer le compte demandé. `git log --oneline --no-merges -3 eb22f4f` reproduit
exactement les trois SHAs observés. La sortie était donc **filtrée, non
fabriquée** : chaque SHA affiché existait bel et bien, aucun n'était le sommet.

**Why:** une sortie filtrée qui ne dit pas qu'elle filtre est indiscernable
d'une sortie complète, et une décision de branchement prise dessus part d'une
base fausse sans signal d'erreur. La première rédaction de cette mémoire
écrivait « des SHAs absents de l'état réel » et « elle ment » : faux, et
précisément la faute que `rules/workflow.md` § Diagnosis discipline interdit —
rapporter l'observation, retenir la cause tant qu'elle n'est pas isolée.
L'observation était « le sommet de `git log` contredit `rev-parse` ». La cause,
nommée trois heures trop tôt, était une invention.

**La portée dépassait git** (roar HET, 2026-08-14) : `wc -l < fichier` rendait 0
sur un fichier de trois lignes, et `head -1 rows.jsonl | log-celebration`
livrait du JSON corrompu au caractère 3, avec un `JSONDecodeError` pour seul
symptôme. Cas plus dur, même jour : un `make -j4 --output-sync=target | grep -c`
comptait 2 invocations d'un garde là où 3 était juste ; le tell était que
`make: Entering directory` sortait *après* le corps de la recette, ce que make
ne fait jamais. **Aucun mécanisme n'est établi pour ces trois-là** : les
symptômes ont disparu avec la montée de version et ne sont plus reproductibles.
Pour le cas `make`, une déduplication de lignes adjacentes explique mieux les
observations qu'une troncature — les lignes perdues étaient identiques, il en
manquait une seule et non une queue, et une troncature ne réordonne pas — mais
cela reste une hypothèse et doit se lire comme telle. Une seule cause est
établie dans cette fiche, celle de git, et elle l'est parce qu'elle se rejoue.

**Passthrough isatty en v0.45.0** (rtk-ai/rtk #1282) : la réécriture est sautée
dès que la sortie n'est pas un terminal. Ce garde est **au-dessus** des commandes
individuelles — d'où l'absence de `IsTerminal` dans `read.rs`, qui n'en a pas
besoin. Conclure à l'absence de garde en grepant le fichier de commande est une
inférence fausse : un contributeur amont l'a faite puis rétractée sur ce même
ticket.

**Conséquence pour un agent, et piège de mesure.** La sortie de l'outil Bash
n'est pas un terminal : `[ -t 1 ]` est faux. Depuis une session d'agent la
réécriture est donc toujours sautée, on lit du brut, et **aucune sonde lancée
depuis l'outil ne peut observer la réécriture** — ni la constater, ni la
disculper. Les sondes « les quatre symptômes ont disparu » passées ici mesuraient
le passthrough et non le correctif ; j'en ai tiré que l'injection `--no-merges`
avait disparu, ce qui était faux. Une session pair, capable de mesurer hors
tube, rapporte qu'en terminal et sans drapeau de limite `--no-merges` reste
injecté (`if !wants_merges && !has_limit_flag`). Invérifiable d'ici : consigné
comme rapport, pas comme fait établi.

Il n'y a donc plus de contournement de pipe à maintenir *pour un agent*, et la
consigne « ne jamais piper de texte structuré » est retirée. Le correctif rend
aussi rtk plus difficile à tester : la façon évidente de capturer une sortie
pour la comparer est précisément celle qui désarme ce qu'on veut mesurer.

**How to apply:** garder rtk à jour ; `rtk --version` est la première chose à
regarder quand une sortie paraît fausse, et `rtk proxy <cmd>` reste le témoin
qui décide si un résultat suspect vient du proxy ou du réel. Ce qui survit au
correctif, parce que c'est vrai quel que soit le proxy : **vérifier par effet,
pas en analysant une sortie.** Pour l'état git qui conditionne une décision,
la plomberie et les codes de retour — `git rev-parse`, `git rev-list --count
A..B`, `git merge-base --is-ancestor` — jamais un SHA lu dans du porcelain.
Ailleurs, provoquer la conséquence et la constater : un compteur de garde se
règle en injectant une citation fantôme dans les trois manuscrits et en
observant les trois compilations échouer et les trois PDF disparaître, verdict
insensible à ce que le proxy fait de stdout. Même famille que
[[feedback-controle-cadence-glob-etroit]] et
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : un contrôle dont le « rien
à signaler » est indiscernable du « je n'ai pas pu regarder » n'est pas un
contrôle.
