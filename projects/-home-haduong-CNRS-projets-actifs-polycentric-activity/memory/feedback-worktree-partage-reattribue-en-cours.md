---
name: feedback-worktree-partage-reattribue-en-cours
description: "Un worktree partagé peut être réattribué à une autre session en cours de tâche — seul le poussé est sûr, et son état ne se rapporte que daté"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 263e4241-7414-43b9-af26-ddf5b9c26ab1
  modified: 2026-08-17T14:56:59.794Z
---

Dans ce dépôt il y a en permanence sept worktrees vivants et plusieurs sessions
parallèles. Le worktree où l'on se tient n'est donc pas à soi : une autre
session peut l'emporter sur sa propre branche pendant qu'on travaille, sans
préavis et sans que rien ne le signale au moment où cela se produit.

**Why:** 2026-08-17, MR #139. Au retour d'un `/gaze` lancé en arrière-plan, le
fichier que je venais d'écrire avait disparu de l'arbre de travail. Le worktree
`t0150-cournot-15032` était passé sur la branche
`het-genealogie-lemme-general`, avec un fichier de note qui n'était pas le mien.
Rien n'avait été perdu, et pour une seule raison : **les deux commits étaient
déjà poussés**. Le tip distant portait la §10 intacte. Le même incident sur un
travail non poussé aurait été une perte sèche, silencieuse, et attribuée à tort
à l'outil de revue.

**L'état d'un arbre partagé ne se rapporte que daté.** J'ai lu `HEAD` à
`b3c9bb7` avec le fichier de note non suivi ; `/gaze`, quelques minutes plus
tôt, l'avait lu à `595941f` avec ce même fichier suivi-et-modifié ; il est
ensuite passé quatre commits plus loin puis s'est détaché sur `origin/main`.
Aucune des deux lectures n'était fausse et aucune n'était un fait : ce sont des
instantanés d'un arbre en mouvement. Rapporter « le worktree est sur X » sans
l'heure, c'est affirmer comme état ce qui n'est qu'une observation.

**How to apply:** pousser avant toute délégation en arrière-plan — un fork qui
tourne dix minutes est dix minutes pendant lesquelles l'arbre peut changer de
mains, et `git push` est le seul verrou qui existe. Au retour d'un fork, relire
`git branch --show-current` et `git rev-parse HEAD` avant la première commande
git qui mute, ce que `rules/git.md` § « Anchor branch-mutating git across a
forked-skill boundary » demande déjà pour une autre raison. Ne pas récupérer un
arbre occupé par une autre session : ouvrir le sien avec
`git worktree add`, et y travailler avec `git -C`. Ne jamais nettoyer un fichier
non suivi qu'on n'a pas écrit. Et vérifier la survie du travail sur le distant
(`git merge-base --is-ancestor <sha> origin/<branche>`), pas dans l'arbre local.
Voir [[feedback-worktree-perime-sert-une-version-ancienne]] pour le cas voisin
du worktree simplement en retard, et
[[feedback-ergprmerge-stale-worktree-after-api-push]].
