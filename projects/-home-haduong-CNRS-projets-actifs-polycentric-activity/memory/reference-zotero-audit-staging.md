---
name: reference-zotero-audit-staging
description: Réconcilier docs/ avec Zotero sans base locale — `zotero-import.py sync-index` puis `audit`, cinq verdicts dont « ambiguous »
metadata:
  type: reference
---

`~/.claude/scripts/zotero-import.py` sait désormais travailler **sans la base
`zotero.sqlite` du client de bureau** (absente sur cette machine, ce qui rendait
tout `match` « unchecked » — donc une reprise en masse rejouait la
bibliothèque entière).

```bash
zotero-import.py sync-index                  # cache de la bibliothèque via l'API web, 24 h, ~9 min
zotero-import.py audit docs/ --out /tmp/a.json
zotero-import.py attach --parent <itemKey> fichier.pdf   # notice existante sans pièce jointe
```

Cinq verdicts : `identical` (md5 identique, rien à faire) — `work_present_with_file`
(l'œuvre est là sous une autre copie) — `work_present_no_file` (**`attach`,
jamais `inject`** : `inject` ne fait que créer, donc il fabrique un doublon) —
`ambiguous` (indice faible : à regarder) — `absent` (`inject`).

**`ambiguous` est une réponse, pas un défaut de réglage.** Sur les 7 cas rendus
ambigus au premier passage, 4 étaient de *vraies œuvres distinctes* (Nordhaus
« Climate Clubs » vs son article de 2018, Végh 2014 vs 2017, l'article
Kabanov-Stricker vs la monographie Kabanov-Safarian, le chapitre Béraud-Numa
chez Routledge vs le chapitre Béraud chez Elgar) : les ranger d'office en
« présent » aurait perdu quatre œuvres en silence.

Le **hachage du contenu** est la clé la plus forte, et seule l'API la porte : il
survit au renommage, au reclassement et à la dérive des métadonnées. Voir
[[feedback-identifiant-scrape-est-une-hypothese]] pour ce qu'il ne faut pas
croire des identifiants, et [[reference-zotero-collection-polycentric]] pour la
collection de dépôt.

État au 19/08/2026 : `docs/` = 289 documents, **285 octet-pour-octet dans
Zotero**. Les 4 restants sont des exclusions motivées (un jumeau pré-OCR, une
table des matières incluse dans un scan complet déjà joint, un scan Internet
Archive moins bon que le PDF éditeur déjà joint, un doublon dont seul un
feuillet de couverture diffère).
