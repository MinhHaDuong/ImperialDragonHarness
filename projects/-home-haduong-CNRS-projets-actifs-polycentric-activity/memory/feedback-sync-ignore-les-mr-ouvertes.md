---
name: feedback-sync-ignore-les-mr-ouvertes
description: "La sonde de synchronisation regarde origin/main et rate le travail parallèle non mergé ; scanner les MR ouvertes sur le sujet avant d'écrire, pas après"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0d11987a-f98d-4cfd-9894-7ed2b7812d33
  modified: 2026-08-17T14:48:59.883Z
---

Avant d'écrire une note ou un passage de fond, scanner les **merge requests
ouvertes** sur le sujet, et pas seulement `origin/main`.

**Why:** la recette de synchronisation en vigueur (`git fetch`, puis
`HEAD..origin/main` et `diff --name-only origin/main...HEAD`) ne voit que ce qui
a **atterri**. Dans ce dépôt, sept MR étaient ouvertes le 2026-08-17, plusieurs
sur des sujets voisins. Une note de généalogie a été rédigée en entier avant que
le contrôle ne révèle que la **MR #131 établissait déjà** la spécialisation du
théorème 1 de Fan aux circuits, et tenait sur Gallai un fait plus fort que celui
que la note avançait. Rien dans la sonde de synchronisation ne pouvait le dire :
#131 n'était pas sur `origin/main`.

La réconciliation a coûté un commit et a bien fini, mais l'ordre était le mauvais
— écrire puis vérifier, au lieu de vérifier puis écrire.

**How to apply:** énumérer les MR ouvertes, puis interroger chacune. Un
`gh pr list --json files` ne peuple pas `files` et rend le même vide qu'une
absence de collision, donc passer par `gh pr view` :

```bash
for n in $(gh pr list --state open --limit 30 --json number --jq '.[].number'); do
  gh pr view "$n" --json title,files --jq '"\(.title)"'
done
```

Lire les **titres** suffit pour repérer le sujet voisin ; ouvrir le corps de
celles qui matchent. Et faire tourner un contrôle positif connu avant de croire
un résultat vide — ici, filtrer sur `conception/` a bien renvoyé quatre MR, ce
qui a prouvé que le scan regardait vraiment. Même famille que
[[feedback-merge-verifier-le-diff-pas-la-sortie]] : un garde dont le « rien
trouvé » est indiscernable de « je n'ai pas pu regarder » n'est pas un garde.
