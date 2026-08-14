---
name: feedback-checkout-ref-ecrase-l-index
description: "git checkout <ref> -- <fichier> écrase l'index en plus de l'arbre de travail, donc détruit les modifications stagées sans avertir"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fabedda1-8499-450e-be83-824460d60108
  modified: 2026-08-14T17:52:41.183Z
---

`git checkout origin/main -- <fichier>` n'est pas une lecture. Il écrit dans
**l'index autant que dans l'arbre de travail**, silencieusement, sans exiger un
arbre propre et sans rien afficher. Des corrections déjà `git add`-ées
disparaissent sans trace récupérable : elles n'ont jamais été committées, donc
il n'y a pas de reflog qui les tienne.

**Why:** pour mesurer la pagination de base du manuscrit, j'ai restauré
`article-het/manuscrit.tex` depuis `origin/main` alors que quatre corrections
étaient stagées. Elles ont été détruites. Il a fallu les refaire à l'identique —
vérifié par diffstat identique, 19 insertions et 11 suppressions — ce qui a
marché ici parce que les quatre tenaient encore en mémoire de session
(2026-08-14, PR #127). Un cran de contexte de plus et le travail était perdu.

**How to apply:** avant toute comparaison avant/après qui restaure un fichier
depuis une ref, committer d'abord — un commit WIP suffit, il se `reset --soft`
ensuite. Pour seulement *lire* une version sans toucher l'index ni l'arbre :
`git show <ref>:<chemin>`. Pour *construire* une version ancienne, ne pas
restaurer dans l'arbre courant du tout : bâtir dans un worktree jetable. La
règle générale est celle de [[feedback-merge-verifier-le-diff-pas-la-sortie]] —
une commande git qui ne dit rien n'a pas pour autant rien fait.
