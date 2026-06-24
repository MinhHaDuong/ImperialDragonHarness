# Memory index — archiveCIRED

## Key insights

- Match Zotero records by identifier (CIR_/ENPC/docid), never by title — the Sachs fonds reuses titles across distinct works.
- Enrichments land in two phases (build then run); `erg-pr-merge` autoclosing on build is a trap — verify a run has landed before treating an enrichment ticket as done.
- The ENPC_LEESU fonds has structurally incomplete metadata (no creator, no date); exclude it from all automated enrichments and completeness audits.
- Zotero rejects `publicationTitle` for non-journalArticle types (HTTP 400); Crossref `container-title` must be mapped type-specifically — same bug exists in HAL and OpenAlex scripts (ticket 0042).
- The committed `tickets/erg` bootstrap binary can lag the installed one; always `erg update` before sweeps and suspect staleness when an erg command "doesn't exist."

## Entries

- [Zotero pivot & catalogue state (2026-06-24)](project_zotero_pivot.md) — HAL deferred; private Zotero group; 686 notices deduplicated; match by id never title; enrichments 0022+0038 done
- [Merge workflow lessons (2026-05-16)](feedback_merge_workflow.md) — squash-merge divergence; guard hook blocks reset --hard on clean tree (ask via `!`); stale committed erg bootstrap binary
- [Index architecture (2026-05-16)](project_index_architecture.md) — file_index.json (1991 files) + doc_index.json (1112 docs); replaces index.json
- [Recueil merge — DONE 2026-06-24](project_recueil_merge.md) — volet complet, all tickets closed; 131↔131 zero-loss proven (0025 GO); group kept+renamed; 18 new docs imported; 8 best-scans marked principal/copy
- [Inari archive mapping](reference_inari_archive_mapping.md) — local archive mirrors inari bucket kCj0pHP0/zotero/www/; recueil bucket Wehurei6 is separate — don't conclude "not on inari" from one bucket
- [LEESU incomplete metadata (2026-06-24)](project_leesu_incomplete_meta.md) — notices sans creator ou sans date sont toutes ENPC_LEESU ; exclure ce fonds des audits de complétude
- [Ticket: none pour housekeeping (2026-06-24)](feedback_ticket_none_housekeeping.md) — PRs qui créent/rouvrent un ticket sans compléter le travail → Ticket: none (pas **Ticket:**)
- [Enrichment build-vs-run gap (2026-06-24)](project_enrichment_build_vs_run.md) — 0023/0024/0038 autoclos sur le build du harnais, pas sur le run ; seul 0022 HAL a enrichi (88) ; vérifier qu'un run a landé avant de croire « fait » (garde 0040)
