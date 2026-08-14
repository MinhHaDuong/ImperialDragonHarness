---
name: feedback-grep-context-audit
description: "Un grep sans fenêtre de contexte n'est pas un audit — les « seven fields » signalés comme bug étaient « no author of the OTHER seven fields », exacts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 08ed2eaf-ca2f-4ccd-b2b6-7bdf52d81a4c
  modified: 2026-08-11T16:09:19.731Z
---

Lors de l'audit terminologique HET (2026-08-11), un grep `seven [a-z]+` a
signalé deux « seven fields » comme reliquats du recomptage seven→eight.
L'agent qui a vérifié EN CONTEXTE a montré qu'ils étaient exacts : « no
author of the *other* seven fields » — vus depuis l'appareil du huitième
champ, les sept autres. Les corriger aurait introduit des erreurs. À
l'inverse, l'audit contextuel a trouvé un vrai reliquat que le grep ne
pouvait pas voir (« six other fields »).

**Why:** Un motif lexical n'a pas de sémantique ; sur du texte savant, les
comptages relatifs (« the other N ») rendent le motif faux dans les deux
sens — faux positifs ET faux négatifs.

**How to apply:** Ne jamais transformer un hit de grep en directive de
correction sans lecture de la phrase ; formuler les consignes de balayage
comme « vérifie en contexte, corrige ou signale » (ce qui a été fait et a
sauvé la mise) ; c'est le pendant textuel de [[feedback-no-inverted-centaur]]
côté machine : escalader vers l'audit contextuel avant de conclure.
