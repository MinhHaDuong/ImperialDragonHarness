---
name: feedback-couper-deplace-le-domicile-de-l-obscurite
description: "Couper une phrase déplace la première occurrence de ses termes ; l'instrument de complexité les refacture au paragraphe suivant, qui se dégrade sans avoir bougé"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc7527c0-fb43-437b-a5a5-49388e9f1de4
  modified: 2026-08-17T15:26:13.308Z
---

**Un terme technique est facturé à sa première occurrence non glosée. Couper la
phrase qui le portait ne le supprime pas : elle le déménage.** Le paragraphe qui
l'accueille voit son score monter alors que pas un mot n'y a changé.

**Why:** le 2026-08-17, la réécriture de l'énoncé dans l'abstract HET a coupé
« The primary texts are all but unconnected. » pour tenir le gabarit EJHET de
100 mots. Le rapport de complexité régénéré a alors fait entrer le paragraphe
194 (revendication d'indépendance) au rang 7 des plus coûteux, de 5,85 à 6,35 :
« primary texts » y faisait désormais sa première occurrence du document, comptée
comme quatrième terme technique non glosé. La moyenne de l'introduction est
montée de 3,83 à 3,87 — pour un abstract devenu plus lisible. Lire ce
mouvement comme une dégradation de la prose serait un contresens : l'obscurité
n'est pas née, elle a changé de domicile, et l'abstract la glosait aussi mal.

**How to apply:** après une coupe dans un texte mesuré par `make complexity`,
régénérer et lire les deux ou trois lignes qui bougent AILLEURS que dans le
passage touché — ce sont les termes qui ont déménagé. Décider alors sur pièce :
gloser le terme à son nouveau domicile, ou constater que l'instrument facture
un mot d'usage courant pour la communauté visée. Le score d'une section n'est
pas un verdict sur la section : c'est un verdict sur l'endroit où le vocabulaire
entre dans le document.

Corollaire de gabarit : quand une contrainte de longueur est atteinte
exactement, toute clarification doit être financée par une coupe, et la coupe a
ces effets à distance — donc chiffrer avant de proposer, et proposer avec les
comptes ([[project-cible-accessibilite-non-specialistes]],
[[feedback-artefact-genere-perime-en-silence]]).
