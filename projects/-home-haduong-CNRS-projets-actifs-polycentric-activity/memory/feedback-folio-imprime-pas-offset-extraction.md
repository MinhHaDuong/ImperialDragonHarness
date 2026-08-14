---
name: feedback-folio-imprime-pas-offset-extraction
description: "Un numéro de page cité se lit sur la page imprimée, jamais interpolé depuis la position dans une extraction pdftotext"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 35c556ec-5ce7-4105-95b3-97264b2339f7
  modified: 2026-08-14T12:06:02.271Z
---

Citer `\citep[p.~262]{Cottle2012}` parce que la phrase apparaissait vers la
ligne 290 d'un `pdftotext` de tout le document, dans un article qui commence
p. 255 et fait ~40 lignes par page. La vraie page était **260** : trouvée en
extrayant page par page (`pdftotext -f N -l N`) et en lisant le folio imprimé
en tête de chaque page (HET, appendice A, note Karush, 2026-08-14).

**Why:** l'extraction concatène le corps, les notes de bas de page, les
en-têtes et les pieds dans un ordre qui n'est pas celui de la mise en page, et
les blocs cités ou les notes cassent toute proportionnalité entre position dans
le flux et numéro de page. L'interpolation donne un nombre plausible et faux —
le pire genre d'erreur, parce qu'un relecteur qui ouvre la page n'y trouve rien
et cesse de faire confiance à l'appareil entier. Dans un manuscrit dont le sujet
*est* la pratique de citation, la note tombe doublement mal.

**How to apply:** pour toute citation à la page, extraire la page seule et
vérifier le folio qu'elle porte — ou rendre la page en image et la lire. Deux
sondes utiles : la ligne de pied donne souvent la pagination officielle de
l'article (ici « Documenta Mathematica · Extra Volume ISMP (2012) 255–269 »,
qui a aussi corrigé la plage bibliographique), et la première page du chapitre
suivant borne la fin du précédent (le chapitre XX du Monograph 13 ouvrant
p. 330 a confirmé Gale–Kuhn–Tucker aux pp. 317–329). Même famille que
[[feedback-grep-context-audit]] et [[feedback-piste-secondaire-lue-sur-piece]] :
la pièce dit ce qui est, l'index dit seulement où il croit que c'est.
