---
name: feedback-revue-cross-repo-cwd-epingle
description: lancer /gaze sur un dépôt B depuis un worktree isolé du dépôt A paralyse le Bash de tout le panel
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-19T20:23:06.527Z
---

Lancé `/gaze` sur une MR du harnais alors que la session était isolée dans un
worktree de `polycentric_activity` (2026-08-19). Chaque agent du panel a hérité
d'un cwd épinglé sur le mauvais dépôt, et le garde d'isolation a refusé
**toutes** ses commandes Bash — jusqu'à `echo`. `EnterWorktree` ne rattrape pas :
le worktree visé appartient à un autre dépôt.

Un agent a contourné par `Read` et `WebFetch`, qui ignorent le garde, et a rendu
une revue en confiance « moyenne » : pas de `git diff` pour vérifier les hunks,
pas de grep de l'arbre. Il l'a dit. Relancée depuis un cwd non épinglé, la même
revue a trouvé six défauts dont deux hauts, invisibles à la lecture seule.

**Why:** une porte de revue qui se dégrade en lecture de fichiers ressemble à
une revue. C'est la même classe que le garde dont le « tout va bien » ne se
distingue pas de « je n'ai pas pu regarder » — sauf qu'ici le coût est un
tampon, pas une alerte manquée.

**How to apply:** avant toute revue croisée-dépôt, sortir du worktree
(`ExitWorktree`, action `keep`) pour désépingler la session. Et lire le rapport
d'un agent qui signale une confiance dégradée comme une demande de relance, non
comme un verdict. Ticket harnais à ouvrir si le cas se répète. Voir
[[feedback-un-test-vert-peut-etre-inatteignable]].
