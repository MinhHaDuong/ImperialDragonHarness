# Memory index — archiveCIRED

## Key insights

- The project pivoted from HAL mass-deposit to a **private Zotero group** to sidestep rights triage; a mature catalogue (inari/Bordignon) already existed, so the work is reconciliation/dedup/enrichment, not bulk import.
- **Match Zotero records by identifier, never by title** — the Sachs fonds reuses titles across distinct works. The same rule in matching code: Jaccard + author/year corroboration, never bare title-containment.
- The data backbone is a **two-layer index**: physical `file_index.json` (1991 files) → logical `doc_index.json` (1112 docs); the old `index.json` is superseded.
- Antonin's "recueil 50 ans" was **mirrored into a My-Library collection** (VPDB49CK, 131 items) instead of joined by a (nonexistent) mapping table; deleting the source group is gated on a zero-information-loss audit (ticket 0025).
- Tooling discipline: every Zotero-writing script needs `--backup` with `--apply`; the **committed `tickets/erg` bootstrap can drift** behind the installed binary (caused a `Label:`/`refresh-STATE.py` failure) — keep it current.

## Entries

- [Zotero pivot (2026-05-16)](project_zotero_pivot.md) — HAL deferred; private Zotero group; catalogue deduplicated 1378→686 (PR #7); match by id never title; 0015 unblocked (mirrored)
- [Merge workflow lessons (2026-05-16)](feedback_merge_workflow.md) — squash-merge divergence; guard hook blocks reset --hard on clean tree (ask via `!`); a missing erg subcommand/header usually means a stale committed bootstrap binary (0027)
- [Index architecture (2026-05-16)](project_index_architecture.md) — file_index.json (1991 files) + doc_index.json (1112 docs); replaces index.json
- [Recueil merge (2026-06-23)](project_recueil_merge.md) — Antonin's group mirrored into collection VPDB49CK (131 items); group deletion FROZEN until ticket 0025 audit confirms zero info loss
