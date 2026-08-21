---
name: feedback-verifier-le-predicat-pas-seulement-le-resultat
description: "Un contrôle dont le « tout va bien » ne se distingue pas du « je n'ai pas su regarder » n'est pas un contrôle — vérifier le prédicat contre un cas connu positif."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0dd7065c-e3cf-4dae-a477-8dae7737aa9a
  modified: 2026-08-21T11:02:20.379Z
---

Deux fois dans la même session (2026-08-21), un contrôle a répondu « rien à
signaler » alors que le défaut était sous ses yeux :

- `check_deploy_units` **exigeait** le symlink qui était précisément la panne
  (`[ ! -L "$dst" ]` → « non symlinkée »). Il validait le défaut au lieu de le
  voir, pendant que sept timers étaient morts depuis deux mois.
- Le détecteur de rattrapage que j'avais écrit une heure plus tôt annonçait
  « aucun — rien n'était dû » pendant que restic scannait 115 GiB.
  `systemctl is-active --quiet` sort **3** sur un `Type=oneshot`, qui reste
  `activating` pendant toute son exécution — donc le test disait « rien ne
  tourne » exactement quand quelque chose tournait, et ne pouvait pas dire
  autre chose.

**Why:** la faute n'est pas d'avoir écrit un mauvais test, c'est d'avoir cru un
résultat négatif sans avoir jamais vu le test répondre positivement. Un
négatif est la sortie par défaut de tout ce qui échoue en silence : mauvaise
commande, mauvais prédicat, mauvais chemin, permission refusée. La règle
harnais le dit déjà pour `gh pr list --json files` ; ces deux instances
montrent que c'est une classe, pas une anecdote sur un outil.

**How to apply:** avant de rapporter « aucune anomalie », faire tourner le
contrôle contre un cas **connu positif** — un fixture délibérément cassé, l'état
réel au moment où le défaut est vivant, ou un mock qui ment dans le bon sens.
En bash, se méfier de `is-active --quiet` (lire `systemctl show -p ActiveState`),
et plus généralement de tout prédicat booléen sur un état qui a plus de deux
valeurs. En test, le cas qui compte est celui qui échoue contre l'ancien code :
c'est le seul qui prouve que le contrôle regarde. Voir
[[project-padme-privileged-ops]].
