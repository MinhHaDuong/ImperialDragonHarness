---
name: project-zotero-pivot
description: archiveCIRED — pivot from HAL deposit to private Zotero group; HAL deferred; catalogue state
metadata: 
  node_type: memory
  type: project
  originSessionId: be1e835b-17e0-441d-84ec-bcb75c0f8549
---

As of 2026-05-16, the project goal shifted from HAL mass deposit to a private Zotero group library shared with CIRED and ENPC researchers.

The private Zotero group **"archive CIRED" already exists** (confirmed 2026-06-19). Credentials live outside the repo in `~/.config/keys/zotero-archive-cired.env`: `ZOTERO_API_KEY`, `ZOTERO_USER_ID`, `ZOTERO_USER_PASSWORD`, `ZOTERO_API_KEY_NAME`. Numeric user ID differs from login — get it via `GET /keys/current`; env var `ZOTERO_USER_LOGIN` holds the login "Base R2DS".

**Why:** HAL requires rights triage (all 741 records had `statut_droits: "inconnu"`) which blocks progress. Zotero private group sidesteps this — no public deposit, no rights barrier.

**Catalogue state (as of 2026-06-24):** My Library **686 deduplicated notices** after dedup (1378→686, PR #7). Reconciliation: 829/1112 archive docs already catalogued (0 orphan keys). Notices link PDFs by URL `inari.centre-cired.fr/.../docs/<name>.pdf` (basename = archive filename, the join key). Scripts: `reconcile_zotero`, `zotero_dedup`, `zotero_relate`, `zotero_tag_collections`. Backups in `outputs/zotero_backup_*.json` (gitignored). Antonin's recueil 50 ans fully integrated (0015/0018/0019 done) — see [[project_recueil_merge]]. Enrichments applied: HAL 88 notices (0022), Crossref 81 nettes (0038).

**How to apply:** Don't plan HAL-related work unless reintroduced. Don't plan a bulk RIS import — the catalogue exists and is deduplicated. Match Zotero records by **identifier (CIR_/ENPC/docid), never by title** — the Sachs fonds reuses titles across distinct works. Dedup invariant: re-parent the PDF onto the master BEFORE deleting a twin. `--apply` on every Zotero-writing script requires `--backup`. Zotero auto-creates the reciprocal `Related` link. Keyless-doc matcher: `src/match_untyped.py`.
