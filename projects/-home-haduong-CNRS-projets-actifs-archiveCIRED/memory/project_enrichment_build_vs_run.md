---
name: project_enrichment_build_vs_run
description: "Enrichment-family tickets were autoclosed on harness BUILD, not on the actual RUN landing in the catalogue — build-vs-run gap"
metadata: 
  node_type: memory
  type: project
  originSessionId: 799884bd-4a18-4465-96d1-4e5723a9c7d1
---

La famille de tickets « enrichir chaque notice via X » (0022 HAL, 0023 OpenAlex,
0024 Web/DDG, 0038 CrossRef) a un *done* en **deux temps** : construire le
harnais (`src/enrich_*.py` + tests) PUIS le lancer et lander les corrections
dans le catalogue Zotero. Au 24 juin 2026, seul **0022 (HAL) a réellement
enrichi** (88 notices). Les trois autres ont été **autoclos sur le seul build** :

- 0023 OpenAlex : run vide, bloqué dès le 1er appel par `BudgetExhausted`
  (budget quotidien gratuit, reset minuit UTC) → 0 notice sur 778. **Réouvert.**
- 0024 Web/DDG : harnais `enrich_web.py` (nommé *web*, pas *google*) construit,
  jamais lancé, aucun output. **Réouvert par l'auteur.**
- 0038 CrossRef : **DONE** — run effectué, 81 corrections nettes dans Zotero
  (135 appliquées − 54 LEESU révoquées). Clos PR #56+#57 (2026-06-24).

**Cause racine** : `erg-pr-merge` ferme tout ticket cité en `**Ticket:**` sans
vérifier les cases d'exit criteria — une PR « harnais seulement » referme donc
le ticket même si « Catalogue enrichi » n'est pas coché.

**Comment l'appliquer** : pour un ticket à *done* en deux temps, découper en
enfants build/run, OU ne mettre que `Ticket-ref:` (pas `**Ticket:**`) dans la
PR qui ne fait que le build. Avant de croire un enrichissement « fait »,
vérifier qu'un run a landé (output + corrections appliquées), pas juste que le
script existe. Garde-fou suivi dans le ticket 0040. Voir aussi
[[feedback_merge_workflow]] (autoclose erg-pr-merge non idempotent).

**Leçons de 0038 Crossref** :
- Score d'appariement < 1.0 = pollution potentielle, pas enrichissement sûr.
  Règle auteur : n'appliquer que les score = 1.0 (exact) ; les 0.75–0.99 sont
  à mettre en attente pour vérification manuelle.
- `publicationTitle` est refusé par Zotero pour `bookSection`, `thesis`,
  `report` (HTTP 400). Le correctif est dans `enrich_crossref.py` ; le même
  bug reste dans `enrich_hal.py` et `enrich_openalex.py` → ticket 0042.
- Le fonds ENPC_LEESU n'a pas de créateurs ni de dates → exclure de tous les
  enrichissements (voir [[project_leesu_incomplete_meta]]).
