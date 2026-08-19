---
name: feedback-un-controle-rouge-accuse-parfois-le-controle
description: "un contrôle qui échoue peut incriminer sa propre méthode et non l'artefact ; distinguer avant de corriger"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-19T10:12:10.332Z
---

À l'extraction de la carte du Handbook (2026-08-19), la vérification d'adresses
a échoué 5 fois sur 5 au volume III et 0 fois sur 10 aux volumes I et II. La
lecture immédiate — « le volume III est mal analysé » — était fausse : le folio
5 mène bien à la page 15 du PDF, vérifié en l'ouvrant. C'est l'instrument qui
ne savait pas trouver la page, parce qu'il indexait les folios par le titre
courant et qu'une page d'ouverture de notice n'en imprime pas.

Le tell : **un échec total et net sur un seul sous-ensemble**, alors qu'un vrai
défaut d'analyse produit des échecs dispersés. 5/5 contre 0/10 décrit une
méthode aveugle sur un cas, pas un artefact faux.

**Pourquoi :** le corpus a déjà quatre formes de « le vert n'est pas une
preuve » ([[feedback-garde-fulltext-aveugle-sans-docs]],
[[feedback-affirmation-negative-sur-source]]). Le rouge demande la même
défiance, et le coût de l'oublier est pire : on « répare » un artefact correct.

**Comment l'appliquer :** avant de corriger l'artefact, éprouver le contrôle
sur un cas connu positif — ici, ouvrir une page à la main. Puis seulement
trancher qui, de la carte ou du vérificateur, se trompe. Voir aussi
[[feedback-folio-imprime-pas-offset-extraction]] : le décalage folio→page est
désormais mesuré par vote de toutes les pages foliotées et reporté avec son
taux d'accord, précisément parce qu'un ancrage unique s'était trompé d'une
unité.
