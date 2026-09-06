---
name: refsbib-suivi-par-git-ici
description: "Dans polycentric_activity, refs.bib est suivi par git (exception à la règle EDM « .bib = staging git-ignoré ») — ne pas le traiter comme un lien ou un fichier jetable"
metadata: 
  node_type: memory
  type: project
  originSessionId: 14e95706-6379-43c3-9201-96a21a5591f1
  modified: 2026-08-30T09:04:00.885Z
---

Dans ce dépôt, `refs.bib` (racine) est **suivi par git** et présent dans chaque
worktree — contrairement à la règle EDM générale qui fait du `.bib` un staging
git-ignoré. Zotero reste le système de référence ; le suivi git sert les
gardes CI (`check_refsbib_note_provenance.py`, `check_cited_fulltext.py`) qui
le lisent dans un checkout frais.

**Why:** le 30/08/2026, un `rm refs.bib` a failli passer inaperçu : la session
croyait supprimer un lien symbolique qu'elle pensait avoir créé (le `ln -s`
avait en réalité été court-circuité parce que le fichier existait). `git
status` a montré ` D refs.bib` — fichier suivi détruit, restauré aussitôt.

**How to apply:** avant de supprimer un fichier qu'on croit avoir créé,
vérifier ce qu'il est (`git ls-files`, `ls -la` — lien ou fichier ?). Dans ce
dépôt, ne jamais « nettoyer » `refs.bib` d'un worktree : il appartient à
l'arbre. Voir [[purge-bib-partagee-casse-les-freres]].
