---
name: reference-recette-pdf-des-notes-jetp
description: Recette pandoc exacte des PDF de conception/ JETP, rétablie sur témoin.
metadata:
  type: reference
---

Les PDF de `climate-finance-het/conception/` (notes JETP et CR de réunion) se
régénèrent avec :

```bash
sed '/^<!--/,/-->$/d' SRC.md > /tmp/x.md   # le bandeau HTML se REND, sinon
pandoc /tmp/x.md -o OUT.pdf --pdf-engine=xelatex --toc \
  -V mainfont=DejaVuSerif -V geometry:margin=2.5cm -V lang=fr \
  --resource-path=conception     # si la note inclut une figure
```

Le CR ajoute `--metadata title="..."` (il a une page de titre) ; les deux notes
n'en ont pas.

Recette rétablie par ajustement contre un **témoin non modifié** — régénérer la
note longue de `origin/main` et comparer la séquence de mots à son PDF committé.
Deux pièges que seul ce contrôle a montrés : la **pagination concordait sur un
réglage faux** (table des matières absente, langue anglaise), et le bandeau de
provenance HTML se rend dans le PDF au lieu d'être ignoré.

Voir [[project-jetp-strate-de-climate-finance-het]].
