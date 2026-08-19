---
name: project-cible-accessibilite-non-specialistes
description: "Les manuscrits d'histoire de la pensée doivent être lisibles par un non-spécialiste ; instrument de mesure et facteurs qui portent réellement le signal"
metadata: 
  node_type: memory
  type: project
  originSessionId: be79e9f1-77d8-4519-968a-dfbe564392eb
  modified: 2026-08-17T14:04:12.016Z
---

Directive auteur du 2026-08-17, après le retour d'un doctorant relecteur sur le
manuscrit HET (« trop érudit ») : **un papier d'histoire de la pensée doit être
accessible aux non-spécialistes**. C'est une cible éditoriale permanente sur ce
dépôt, pas une remarque ponctuelle sur un paragraphe.

**Ne pas mesurer ça avec un indice de lisibilité.** L'érudition n'est pas
l'illisibilité : un paragraphe de phrases courtes reste fermé au non-spécialiste
s'il nomme cinq personnes inconnues et mêle le vocabulaire de trois champs. Les
trois mesures qui portent le signal sur ce corpus sont *les noms propres
introduits pour la première fois*, *les termes techniques inédits*, et *le
nombre de champs de vocabulaire mêlés dans un paragraphe* — pas Flesch, pas la
longueur de phrase, qui n'arrivent qu'ensuite.

**Instrument** : `scripts/score_prose_complexity.py` + `scripts/prose-complexity.toml`
(barème et lexique ; le code ne porte aucune constante). `make complexity` écrit
`conception/rapport-complexite-<manuscrit>.md`. `--compare` sur un JSON antérieur
mesure l'effet d'une passe de réécriture. Livré par la MR #134.

Il lit **LaTeX et Quarto** (`--flavour`, déduit de l'extension), éprouvé sur les
cinq manuscrits `.qmd` de climate-finance-het. Il vit dans polycentric_activity ;
le promouvoir dans l'IDH reste possible et non fait — arbitrage auteur en attente.

**Le geste de correction est celui du ticket 0026** (passe P1 pour référé JET) :
glose à la première occurrence, un vocabulaire par paragraphe, apparat en note,
exemple filé, paraphrase « In words: ». Voir aussi
[[project-het-hand-pagination]] : toute réécriture HET §3 déborde la page.

**Bandes du 2026-08-17** (`conception/rapport-calibrage-complexite.md`), corpus
de 286 PDF moissonnés en accès libre via OpenAlex, 26 502 paragraphes. Part des
paragraphes de niveau C+ par article, IC 95 % :

| histoire de la pensée éco | 34,7 % [30 ; 39] | n = 54 |
| **manuscrit HET** | **30,6 %** | 1 |
| working paper éco | 26,1 % [23 ; 29] | n = 83 |
| grande revue d'éco | 23,4 % [20 ; 27] | n = 85 |

**Le manuscrit est au percentile 47 de son propre champ, donc au milieu**, et
60–62 des littératures voisines. La plainte du doctorant lit un écart de
*genre*, pas une singularité du manuscrit : le rendre facile à un lecteur
d'économie appliquée reviendrait à l'écrire moins dense que son champ, ce qui
est un choix éditorial et non une correction de défaut.

**Le profil compte plus que la médiane.** Le manuscrit a la queue dure la plus
courte (D 10 % contre 17 % dans son champ) et la bande C la plus épaisse
(21 %). Il n'est pas érudit par pics, il est uniformément moyen-dense : le
travail utile est de convertir des C en A ou B (ajouter des respirations, geste
du ticket 0026), pas de traiter les douze paragraphes de niveau D.

Autres manuscrits du dépôt, même barème : MIMO est le plus dense ;
climate-finance-het va de 5 % (papier « agentic ») à 29 % (manuscrit principal).

**Mesurer un PDF publié demande un contrôle positif, jamais une mesure nue.** Le
manuscrit existe en source et en PDF : les deux doivent concorder (35,6 / 36,4),
et c'est ce contrôle qui a fait rejeter trois découpages successifs par ailleurs
verts. Cinq artefacts d'extraction rendaient des chiffres plausibles et faux —
fac-similé sans couche texte, tirets conditionnels invisibles, entrée de
bibliographie prise pour un titre, interligne double, absence d'alinéas.
