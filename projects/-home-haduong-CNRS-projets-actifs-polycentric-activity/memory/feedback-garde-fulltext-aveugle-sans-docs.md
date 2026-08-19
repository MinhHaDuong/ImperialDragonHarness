---
name: feedback-garde-fulltext-aveugle-sans-docs
description: "Dans un worktree, make lint rend « clean » sans avoir contrôlé l'existence des PDF ; monter docs/ en lien symbolique avant de conclure"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 277b597a-6ee8-4d6c-8821-ab09a6962263
  modified: 2026-08-18T09:33:40.996Z
---

`docs/` est git-ignoré, donc **absent de tout worktree fraîchement créé**.
`scripts/check_cited_fulltext.py` y dégrade proprement — il imprime
« fulltext existence NOT checked (fresh worktree or CI) » — mais la ligne
précédente dit `clean`, et c'est celle qu'on lit.

Recette avant toute conclusion sur le câblage de `refs.bib` :

```bash
ln -sfn /home/haduong/CNRS/projets/actifs/polycentric_activity/docs docs
make lint          # doit dire « clean » SANS « existence checks skipped »
rm docs            # le lien n'est pas couvert par « docs/ » dans .gitignore
```

Le lien symbolique apparaît en `?? docs` au `git status` : le motif
`.gitignore` vise un répertoire, pas un lien. Le retirer avant de commiter.

**Why:** le 2026-08-18, le contrôle de redondance de l'allowlist est resté
vert alors que `Koopmans1949` venait de recevoir son `file=` et aurait dû
faire rougir le garde. Sans `docs/`, la moitié « existence » ne s'exécute
pas, et le contrôle de redondance en dépend. Une fois `docs/` monté, le
garde a rougi au bon endroit puis verdi après retrait de la ligne — c'est
cette paire rouge/vert qui prouve quelque chose, pas le vert seul.

**How to apply:** monter `docs/` pour tout travail touchant `file=`,
l'allowlist ou la discipline 0013 ; et ne jamais rapporter « lint vert »
sans dire si le contrôle d'existence a tourné. C'est l'instance concrète
de [[feedback-ligne-sans-clause-disculpatoire]] et de la règle générale
qu'un garde dont l'« tout va bien » est indiscernable de « je n'ai pas
regardé » doit s'éprouver sur un cas positif connu.
