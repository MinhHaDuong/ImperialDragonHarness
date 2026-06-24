---
name: project_recueil_merge
description: "Recueil volet COMPLETE (2026-06-24): Antonin's Recueil_CIRED group mirrored into My-Library collection VPDB49CK (131), zero-loss proven, group kept+renamed, all tickets closed"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9ab720bf-5060-4796-8455-6c9e7417e171
---

**VOLET RECUEIL TERMINÉ (2026-06-24)** — tickets 0015, 0018, 0019, 0025, 0029 tous fermés.
- 0025 (audit zéro-perte) clos **GO** : bijection injective 131↔131 + audit champ-à-champ.
  Le groupe n'est PAS supprimé : conservé, renommé `Recueil_CIRED_tout_importé` (trace).
  Plan en avant = copier les docs CIRED sur une bibliothèque adossée ENPC (0037/0030).
- 0019 : corrections d'Antonin propagées (1 vraie : +2 auteurs sur Z83SYUK5) ; les faux
  positifs étaient du bruit typographique. Publications distinctes liées (`relations`), pas fusionnées.
- 0018 : 18 docs nouveaux au catalogue (13 importés via Crossref/HAL DOI + 2 grises saisies
  depuis les PDF ; tag `recueil-50ans-ajout-0018`, hors VPDB49CK). 8 meilleurs scans tranchés :
  2 fichiers gardés par notice, `url`=principal / `extra`=l'autre marqué (« moins bonne copie » ou source).
- Audit (`verify_recueil_mirror.metadata_missing`) durci : tolère les étiquettes typo (`vol.`/`n°`/`p.`).

Historique ci-dessous (état au 2026-06-23, avant clôture) :

Antonin's separate Zotero group `Recueil_CIRED` (id 2511149, 131 notices) was the
"recueil 50 ans CIRED" selection. Decision (not a separate group): **mirror it into
My Library** (userID 2114597) as collection **"Recueil 50 ans CIRED" key VPDB49CK**
plus tag `recueil-50ans`. This replaces [[project_zotero_pivot]]'s blocked 0015.

State as of 2026-06-23 (PRs #9–#15 merged to main):
- Collection VPDB49CK holds **131 items**: 53 title-strong matches reconciled (tag links
  existing notices), 78 group notices injected as fresh copies, 69 PDF/URL links attached
  (tag `à-dédoublonner`). 4 bad author+year reconciliations were reverted → 5 notices.
- Tooling on main: `select_new_recueil.py`, `build_recueil_ris.py`, `diff_recueil.py`
  (+`report_to_ledger`), `apply_corrections.py`, `add_new_docs.py`, `match_untyped.py`.
- 12 corrections applied to live My Library (4 manual PDF/HAL-verified + 8 "sûr").

**GATE — do not delete the group** `Recueil_CIRED` until ticket **0025** (read-only
independent audit) returns *zero information loss*: every field + PDF/URL of each of the
131 group notices must be covered by some My-Library notice. Dedup of the ~48+ injected
duplicates is explicitly OUT of 0025's scope (deferred, `src/zotero_dedup.py` exists).

Tracker **0015** stays open (children 0018 ingest, 0019 propagate — both still open).
0018's 13 non-recueil new-content docs: injection paused. Enrichment swarms: 0021
(author normalization), 0022 HAL, 0023 OpenAlex, 0024 Google.

Matching rule learned: use **Jaccard + author/year corroboration**, never bare
title-containment — containment inflated a Godard/Hourcade pair to 0.75 (Jaccard 0.25).
`diff_recueil.py` fixed; `match_untyped.py` still uses `max(jaccard, containment)` but
guarded by `smaller>=4` for legitimately-truncated filenames — latent containment-without-
corroboration path in `score()` tracked by **ticket 0026** (not yet a confirmed defect).
