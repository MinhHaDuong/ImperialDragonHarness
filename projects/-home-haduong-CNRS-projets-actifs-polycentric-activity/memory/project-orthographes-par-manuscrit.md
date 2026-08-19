---
name: project-orthographes-par-manuscrit
description: "Chaque manuscrit du dépôt tient sa propre variété d'anglais, imposée par sa venue ; HET est en britannique -ise, les deux frères sont cohérents et ne doivent pas être uniformisés"
metadata: 
  node_type: memory
  type: project
  originSessionId: bc7527c0-fb43-437b-a5a5-49388e9f1de4
  modified: 2026-08-17T15:44:22.542Z
---

**Les trois manuscrits ne partagent pas la même orthographe, et c'est correct.**
Une passe d'uniformisation qui les traiterait ensemble casserait deux textes sur
trois.

- `article-het` — **britannique en « -ise »**, imposé par les Style Guidelines
  d'EJHET et consigné au § 11 de `conception/checklist-venue-ejhet.md`. Passe
  appliquée le 2026-08-17 : 62 occurrences converties.
- `article-no-arbitrage` — **américain**, cohérent (realized, neighbors,
  favorable, normalization). Aucun résidu britannique.
- `article-mimo-protocole` — **britannique d'Oxford**, cohérent : -our et -lled
  (labour-power, modelled, unmodelled) avec -ize (maximizer, decentralized).
  Ses seuls « center » sont du LaTeX (`\centering`, `align=center`), pas de la
  prose. À ne pas toucher.

**Why:** l'oxfordien est une variété légitime, pas un mélange — c'est
exactement ce qu'était HET avant la passe (britannique partout, -ize compris),
et le diagnostic « le manuscrit est mixte » était donc trop sévère : la
conversion tient à une exigence de venue, pas à un défaut de tenue. Le
distinguo compte parce qu'il décide si un frère doit être balayé ou laissé.

**How to apply:** avant toute passe orthographique, lire la checklist de venue
du manuscrit visé, et ne jamais étendre la passe aux frères. Deux exceptions
tenues dans HET, à ne pas défaire : le titre publié *Network Flows and
Monotropic Optimization* (l'orthographe de couverture fait foi) et *prize*, hors
famille. Sonde de contrôle : `\w+iz(e|ed|ing|ation)` doit ne rendre que quatre
*prize* et ce titre.

Voir [[feedback-couper-deplace-le-domicile-de-l-obscurite]] pour l'effet
collatéral d'une retouche sur les rapports engendrés, et
[[feedback-artefact-genere-perime-en-silence]] pour la régénération à faire dans
le même lot.
