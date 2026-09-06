---
name: carte-pas-de-garde-de-coherence
description: Arbitrage auteur 2026-08-20 — pas de garde de cohérence interne pour les artefacts de la carte du champ ; ne pas re-proposer
metadata: 
  node_type: memory
  type: project
  originSessionId: 7a40c198-2d4c-4fef-85b3-5a06591f74b9
  modified: 2026-08-20T11:52:20.763Z
---

Le ticket 0301 (« garde de fraîcheur des artefacts de la carte du champ »)
a été fermé **wontfix** par arbitrage auteur le 2026-08-20 (MR #188). La
demande venait d'une remarque de revue de la MR #183 ; la clarification a
montré qu'il s'agissait d'une garde de cohérence interne (canon = carte,
folios, compteurs, renvois), pas de fraîcheur — la source (Handbook Elgar
2016) est figée. L'auteur a jugé la garde non nécessaire.

**Conséquence pour les balayages** : ne pas re-déposer de ticket proposant
une garde pour `handbook-map.md` / `handbook-canon.md` /
`handbook-map-data.json`. Une divergence constatée se corrige en
régénérant (`make handbook-map`), pas en ajoutant un garde permanent.

Voir [[carte-du-champ-handbook]] pour la carte elle-même.
