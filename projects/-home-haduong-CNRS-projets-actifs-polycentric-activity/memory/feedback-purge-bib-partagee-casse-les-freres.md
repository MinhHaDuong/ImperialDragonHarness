---
name: feedback-purge-bib-partagee-casse-les-freres
description: "refs.bib est partagé par les quatre manuscrits — une purge scopée à un seul en casse un autre, et seul le build du frère le révèle"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 54ae158a-3514-4772-a0ad-9dc3f35e48fb
  modified: 2026-08-14T09:10:02.028Z
---

`refs.bib` à la racine sert `article-het`, `article-no-arbitrage`,
`article-mimo-protocole`. Une purge d'entrées « non citées » calculée sur
un seul manuscrit supprime des entrées qu'un frère cite encore. La purge
HET R48 a ainsi retiré `Afriat1967`, que P1 cite toujours ; le bloc de
restauration a rattrapé `Beckmann1952`, `TakayamaJudge1971` et
`Chacholiades1971` mais pas celle-là, et `origin/main` est resté cassé
plusieurs jours (2026-08-14, découvert en intégrant la MR #38).

**Why:** la casse est muette. LaTeX compile, le PDF sort, la pagination
ne bouge pas — seul le `.blg` porte `Warning--I didn't find a database
entry for "X"` et le `.log` une citation indéfinie. Aucun test ne la
voit, et le manuscrit rend `(?)` à la place de la référence. Pire, une
fusion à trois voies propage fidèlement la suppression : une branche qui
détient encore l'entrée a l'air de vouloir *revenir en arrière* sur main,
alors qu'elle porte le correctif.

**How to apply:** après toute purge ou tout conflit sur `refs.bib`,
construire **tous** les manuscrits qui le lisent et vérifier chaque
`.blg` (`grep -i "didn't find"`) et chaque `.log`
(`grep -c "Citation.*undefined"`) — pas seulement celui qu'on édite.
`make all` suffit à les produire. Et quand une fusion fait disparaître
une entrée, établir d'abord si `origin/main` est déjà cassé — extraire
`git show origin/main:refs.bib` et le tex du frère dans un répertoire
jetable et compiler — avant de conclure que la fusion en est la cause :
ici le défaut préexistait et la branche en détenait le correctif.
Complète [[feedback-merge-verifier-le-diff-pas-la-sortie]] : le diff dit
ce que la fusion change, le build du frère dit ce qu'elle casse.
