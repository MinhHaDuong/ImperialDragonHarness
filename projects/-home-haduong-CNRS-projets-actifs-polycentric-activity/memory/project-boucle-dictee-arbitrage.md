---
name: project-boucle-dictee-arbitrage
description: "Le circuit de dictée d'arbitrage prose — registre sur main, équipe résidente ré-adressable, une seule PR, PDF régénéré à chaque lot — a traité 50 remarques en une séance"
metadata: 
  node_type: memory
  type: project
  originSessionId: 08ed2eaf-ca2f-4ccd-b2b6-7bdf52d81a4c
  modified: 2026-08-11T16:09:39.561Z
---

Séance HET du 2026-08-11 : l'auteur a dicté 50 remarques en continu
(structure, coupes de gabarit ligne à ligne, terminologie, biblio) pendant
que le manuscrit était révisé. Le circuit qui a tenu :

1. Chaque remarque est consignée **verbatim** au registre daté de
   `conception/` (micro-PR sur main, numérotation continue) — le registre
   est la spécification et le ledger de couverture.
2. Une **équipe résidente** (team-lead ré-adressé par messages successifs,
   jamais relancé à froid) exécute sur **une seule branche/PR** avec table
   de couverture remarque→changement dans le body.
3. Livraison = PDF propre régénéré **au même chemin** — l'auteur arbitre
   sur le rendu, jamais sur un diff.
4. Les questions de l'auteur reçoivent une **instruction d'enquête**
   (« vérifie en contexte, corrige ou signale ») — deux fausses alertes
   évitées, un vrai bug trouvé ([[feedback-grep-context-audit]]).

**Coût connu du circuit** : ~15 micro-PR de registre en une séance (une par
remarque) — acceptable mais lourd ; en cas de dictée dense, batcher les
remarques consécutives dans un même commit de registre quand elles arrivent
à moins de quelques minutes d'écart. À réutiliser pour les prochains rounds
de prose (P1/JET, MIMO) ; s'articule avec [[project-zotero-injection-auto]]
pour la partie acquisitions (guetteur ~/Downloads + page de travail HTML,
qui a soldé 5 textes JSTOR en séance).
