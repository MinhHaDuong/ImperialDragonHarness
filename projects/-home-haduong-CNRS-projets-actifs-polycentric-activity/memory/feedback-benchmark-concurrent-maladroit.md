---
name: feedback-benchmark-concurrent-maladroit
description: "une économie mesurée contre un concurrent maladroit n'est pas une propriété de l'outil — le bras rival peut apprendre entre deux mesures"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-20T17:42:35.140Z
---

Bench carte HET, août 2026 : en v1 la carte « économisait » 24 % de tokens et
25 % de temps face aux PDF nus ; en v2 elle en coûtait 60 % de plus. Rien
n'avait changé côté carte. Le bras PDF, lui, avait découvert le `grep` sur
les extraits texte (115 appels → 25) : l'économie mesurée en v1 n'était pas
une propriété de l'index mais de l'ignorance du concurrent.

**Why:** un avantage comparatif mesuré une fois est attribué à l'outil, alors
qu'il peut appartenir à la baseline. Toute conclusion « X est plus efficace
que Y » est conditionnelle à la stratégie de Y ce jour-là — et les agents
changent de stratégie d'un tirage à l'autre sans qu'on le leur demande.

**How to apply:** avant d'inscrire « X économise Z % », lire *comment* le
bras concurrent a travaillé (ses appels d'outil), pas seulement combien il a
coûté. Si sa stratégie est visiblement sous-optimale, le noter comme borne
haute, pas comme propriété. Refaire la mesure quand la baseline s'améliore.
Voir [[project-carte-du-champ-handbook]].
