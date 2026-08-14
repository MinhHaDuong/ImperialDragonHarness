---
name: feedback-ligne-sans-clause-disculpatoire
description: "Dans une table de preuves faite à la main, la ligne qui ne porte pas la clause que toutes ses sœurs portent est le défaut"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 81befdb7-37e9-46db-8115-1200addcda78
  modified: 2026-08-14T09:38:43.892Z
---

Pour auditer une table de preuves construite à la main, ne pas relire chaque
ligne isolément : comparer les lignes entre elles et chercher **celle qui ne
peut pas dire ce que ses sœurs disent**. L'auteur d'une table honnête ajoute
spontanément une clause disculpatoire là où le verdict le mérite ; là où il
l'omet, c'est souvent qu'elle serait fausse.

**Why:** 2026-08-14, balayage `/roar` sur `tab:citations` du manuscrit HET.
La ligne « Koopmans 1951 » donne le verdict `none` à la colonne « cite-t-il
une autre découverte ? » tout en listant « Samuelson (1949 RAND ms.) » dans sa
propre colonne détail — Samuelson étant auteur d'une des huit communautés
comptées. Ce qui a transformé un soupçon en certitude n'est pas la lecture de
la ligne, c'est la comparaison : **toutes** les autres lignes `none` portent
une clause explicite — « no author of the eight communities », « no
economist », « Kantorovich absent », « his own 1966 paper absent ». Celle-là
est la seule sans, et la ligne symétrique (Samuelson 1952) compte bien
Koopmans comme citation croisée dans l'autre sens. L'asymétrie était interne
à la table, visible sans aucune source externe.

**How to apply:** sur toute table de vérification (registre de sources, matrice
de citations, grille de conformité), extraire la colonne verdict, grouper par
valeur, et lire les colonnes justificatives du groupe le plus favorable côte à
côte. La ligne dépareillée est le premier endroit à instruire. Se combine avec
[[feedback-piste-secondaire-lue-sur-piece]] : la table dit ce qu'elle a, la
pièce dit ce qui est.
