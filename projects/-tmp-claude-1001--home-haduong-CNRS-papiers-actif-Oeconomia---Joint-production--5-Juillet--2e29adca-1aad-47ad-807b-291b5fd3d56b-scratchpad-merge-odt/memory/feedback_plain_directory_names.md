---
name: plain-directory-names
description: "Nommer les répertoires de workpackages en clair, jamais par codes opaques (p1/p3/het)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1848c079-892d-4cc3-aff1-bf176e1c7e39
---

Les répertoires de workpackages dans les programmes de papiers se nomment en
clair, par leur contenu (ex. `marches-carbone/`, `arbitrage-onchain/`,
`sept-costumes/`), jamais par les codes du programme (`p1/`, `p3/`, `het/`).

**Why:** Demandé explicitement par Minh (2026-07-06, organisation de
polycentric_activity) : les codes P1/P3/P5/HET sont des identifiants de
programme — ils vivent dans les notes de conception et les titres de tickets,
pas dans l'arborescence.

**How to apply:** À la création de la structure multi-papiers d'un dépôt,
proposer des noms descriptifs et garder les codes uniquement comme références
croisées dans les tickets/notes. Voir [[prose-vs-code-workflow]].
