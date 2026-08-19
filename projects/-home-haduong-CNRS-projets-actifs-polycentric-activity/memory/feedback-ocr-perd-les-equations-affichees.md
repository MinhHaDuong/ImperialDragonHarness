---
name: feedback-ocr-perd-les-equations-affichees
description: "Une couche de texte perd parfois les équations en silence ; sonder avant de conclure sur le contenu formel d'une source"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1e742b5d-6433-44f8-b6a3-8dbb03a621ba
  modified: 2026-08-17T13:21:58.842Z
---

La couche de texte d'un fac-similé perd **parfois** les équations affichées,
sans rien signaler. Le défaut est réel et il n'est pas universel : c'est un
avertissement, pas une loi, et la sonde vaut mieux que l'interdit.

**Why:** mesuré sur quatre fac-similés du corpus le 2026-08-17, pp. 5-12
extraites. Cournot 1838 (scan BnF) rend 421 caractères et **zéro** ligne portant
`=` ; Walras 1900 (recodé LuraDocument) rend 24 522 caractères de prose et
**zéro** équation ; Beckmann 1952 (océrisé par `ocrmypdf`) en garde 58 lignes et
Afriat 1967 en garde 36. Deux sur quatre. Le cas Walras est le plus instructif,
la prose passant entière pendant que les displays disparaissent. **La cause n'est
pas isolée** — quatre documents ne disent pas ce qui sépare les deux groupes — et
elle ne doit pas être devinée. Une première version de cette entrée décrétait la
perte générale, sur un seul document ; l'auteur l'a relevé comme un jugement à
l'emporte-pièce, et il avait raison.

**How to apply:** quand une affirmation porte sur le **contenu formel** d'une
source et non sur sa prose, sonder d'abord : extraire les pages visées et compter
les lignes portant `=`. Prose abondante et zéro équation est la signature du cas
défaillant. Rendre alors la page (`pdftoppm -png -scale-to 1500`) et la lire —
une lecture optique sémantique vaut mieux qu'un grep hâtif sur l'extraction. Le
corollaire tient même quand l'extraction paraît saine : un grep ne peut pas
trouver une formule qui n'a jamais été extraite, donc un résultat nul n'est pas
un constat négatif. Voir [[feedback-chercher-le-contenu-pas-le-vocabulaire]].

Coût du raccourci : la couche OCR de Cournot 1838 ch. III ne portait ni la bande,
ni la condition de cycle, ni le potentiel, c'est-à-dire exactement les énoncés en
cause dans l'arbitrage. Distinct de
[[feedback-folio-imprime-pas-offset-extraction]], qui porte sur *quelle* page
citer ; ici la question est si le contenu s'y trouve. Les deux se règlent sur
l'image.
