---
name: project_recueil_merge
description: "Antonin's Recueil_CIRED group mirrored into a My-Library collection (131 items); group deletion FROZEN until ticket 0025 audit returns zero information loss"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9ab720bf-5060-4796-8455-6c9e7417e171
---

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
