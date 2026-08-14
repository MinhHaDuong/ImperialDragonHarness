---
name: feedback-ligne-sans-clause-disculpatoire
description: "Dans une table de preuves faite à la main, la ligne qui ne porte pas la clause que toutes ses sœurs portent est le défaut"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 81befdb7-37e9-46db-8115-1200addcda78
  modified: 2026-08-14T12:20:02.677Z
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
comptées. La comparaison entre lignes est bien ce qui a levé le lièvre.

**Correction du même jour, sur relecture de la table.** La première version de
cette mémoire disait que la ligne Koopmans était « la seule sans clause
disculpatoire ». C'est faux : elle porte « Kantorovich absent » — que le
paragraphe citait pourtant, à tort, comme la clause *d'une autre* ligne. La
formulation exacte du défaut est plus fine, et c'est elle qu'il faut retenir :
la ligne Koopmans est la seule qui **ne puisse pas** porter la clause forte de
ses sœurs, « no author of the eight communities », parce que Samuelson en est
un ; sa clause réelle ne nomme qu'une autre absence et détourne le regard de
la présence qu'elle vient d'imprimer. Le verdict `none` s'est d'ailleurs
révélé défendable, la table comptant entre énoncés recensés et le mémorandum
de 1949 n'en étant pas un — le défaut est une convention non écrite, pas une
erreur de compte.

Leçon de la correction : « aucune clause » et « une clause qui ne peut pas
être la bonne » se ressemblent à la lecture rapide et ne demandent pas la même
réparation. Vérifier laquelle des deux avant d'écrire le constat.

**How to apply:** sur toute table de vérification (registre de sources, matrice
de citations, grille de conformité), extraire la colonne verdict, grouper par
valeur, et lire les colonnes justificatives du groupe le plus favorable côte à
côte. La ligne dépareillée est le premier endroit à instruire. Se combine avec
[[feedback-piste-secondaire-lue-sur-piece]] : la table dit ce qu'elle a, la
pièce dit ce qui est.
