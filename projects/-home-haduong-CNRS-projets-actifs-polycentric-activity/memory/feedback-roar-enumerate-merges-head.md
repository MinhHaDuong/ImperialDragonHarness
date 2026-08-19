---
name: feedback-roar-enumerate-merges-head
description: "enumerate-merges.py vise HEAD en dur, donc un /roar lancé depuis le worktree de la branche sous-compte les merges sans rien signaler"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6bf9eb38-db72-43dc-ae95-d8d805ba527d
  modified: 2026-08-14T13:49:32.185Z
---

`skills/roar/enumerate-merges.py` énumère `<sentinelle>..HEAD`, avec `HEAD` en
dur — pas d'argument pour viser une autre référence. Or `/roar` tourne
normalement depuis le worktree de la branche qu'on vient de faire merger, et
ce worktree est resté sur la **pointe de la branche**, en deçà du commit de
merge. L'énumération manque donc la MR qu'on vient justement de célébrer, et
toutes celles landées entre-temps.

Le 2026-08-14 elle a rendu 3 entrées au lieu de 4 : la MR #124, mergée
quelques minutes plus tôt, était absente. Rien ne le signale — la sortie est
bien formée, simplement incomplète.

**Why:** c'est encore la forme « le tout-va-bien est indiscernable du je-n'ai-pas-
regardé », ici appliquée à la télémétrie : une énumération courte ne se
distingue pas d'une énumération juste. Le coût est une perte d'attribution par
ticket, ce que la sentinelle par MR (ticket harnais 0331) existait précisément
pour éviter.

**How to apply:** avant l'étape 2 de `/roar`, détacher le worktree sur la
référence à jour — `git fetch origin && git switch --detach origin/main` — puis
énumérer. Vérifier que le compte inclut la MR qu'on vient de merger ; si elle
manque, `HEAD` est en retard. Sous le seuil de gravité (télémétrie, pas un
gate), donc noté ici plutôt que ticketé — à remonter au harnais si le cas se
répète.

Voisin : la sentinelle harnais était 17 merges en retard le même jour, signe
que des sessions mergent sans roarer. Les 17 ont été journalisés d'un coup.
Voir [[feedback-subagent-model-effort-levers]].
