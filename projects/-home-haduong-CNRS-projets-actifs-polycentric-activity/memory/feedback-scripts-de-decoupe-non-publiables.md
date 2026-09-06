---
name: feedback-scripts-de-decoupe-non-publiables
description: "Les scripts split_handbook_md.py / split_palgrave_md.py ne sont pas publiables — ils sont inséparables d'ouvrages non redistribuables ; ne pas reproposer de les copier"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fe6e7540-c11a-418f-b7b6-a5a5034638e8
  modified: 2026-08-21T11:27:42.505Z
---

`scripts/split_handbook_md.py` et `split_palgrave_md.py` restent dans le dépôt
privé **parce qu'ils s'appliquent à des PDF non redistribuables**, pas par
préférence de rangement. Ne pas reproposer de les copier vers un dépôt public.

**Pourquoi**, vérifié sur pièce le 2026-08-21 :

- ils **nomment les ouvrages** dans leur docstring (5 et 6 occurrences), ce qui
  casse à lui seul la politique de nommage du dépôt public ;
- ils ne sont pas des outils de texte génériques : ils consomment
  `conception/handbook-map-data.json` — bornes de notices, auteurs, renvois,
  décalages de pagination par volume — pour produire un dérivé structuré de ces
  PDF précis. Le couple script + carte est une machine à débiter *cet*
  ouvrage-là ;
- publier la carte serait publier l'appareil éditorial de l'ouvrage (196
  notices, 1613 renvois).

**How to apply :** dans `corpus-access-bench`, l'absence de ces scripts se
**motive** au lieu de s'excuser — le dépôt décrit la découpe et ne la livre pas,
parce que la livrer reviendrait à outiller la reproduction d'une œuvre protégée.
Ce qui fermerait vraiment l'écart est un découpeur générique (PDF quelconque +
carte de structure fournie par l'utilisateur → un fichier par entrée), à écrire,
pas une copie. Voir [[feedback-affirmation-negative-sur-source]] pour le réflexe
de vérifier avant d'affirmer, et [[project-carte-du-champ-handbook]] pour la
carte elle-même.

Coût de ne pas l'avoir su : la même proposition inutile faite trois fois dans
une seule session, chaque fois présentée comme « une ligne de `cp` ».
