---
name: project-zotero-pivot
description: archiveCIRED — pivot from HAL deposit to private Zotero group; HAL deferred
metadata: 
  node_type: memory
  type: project
  originSessionId: be1e835b-17e0-441d-84ec-bcb75c0f8549
---

As of 2026-05-16, the project goal shifted from HAL mass deposit to a private Zotero group library shared with CIRED and ENPC researchers.

The private Zotero group **"archive CIRED" already exists** (confirmed 2026-06-19). Credentials live outside the repo in `~/.config/keys/zotero-archive-cired.env`: `ZOTERO_API_KEY`, `ZOTERO_USER_ID`, `ZOTERO_USER_PASSWORD`, `ZOTERO_API_KEY_NAME` (the variable names had a `ZOERO_`→`ZOTERO_` typo, fixed). Open question for ticket 0008: confirm the **group ID** (distinct from userID; needed for `/groups/<groupID>/items`) — may need `GET /users/<userID>/groups` and adding `ZOTERO_GROUP_ID` to the env file.

**Why:** HAL requires rights triage (all 741 records had `statut_droits: "inconnu"`) which blocks progress. Zotero private group sidesteps this — no public deposit, no rights barrier.

**Reconciliation finding (2026-06-19):** a *mature* Zotero catalogue already exists — 1378 personal notices + group `Recueil_CIRED` (id 2511149) — almost certainly the inari/CIRED_numerisation work (F. Bordignon). Notices link PDFs by URL `inari.centre-cired.fr/.../docs/<name>.pdf` whose basename is the archive filename (the join key with our doc_index). `src/reconcile_zotero.py` (PR #7) crosses the two: **829/1112 docs already catalogued, 0 orphan keys, structured fonds ~100% covered**, only `CIR_GOD_0017` missing, 282 docs without an archive key (type=null/non-classifié) still to match by title/author. So bulk import is dead; remaining 0008 work is the 282 title-match + gap-filling + metadata audit. Note: env var `ZOTERO_USER_LOGIN` holds the login "Base R2DS" (renamed from the misleading `ZOTERO_USER_ID`), not the numeric id — get the numeric id via `GET /keys/current`.

**Dedup done (2026-06-19, PR #7, tickets 0013/0014/0016/0017 closed):** My Library **1378 → 686 notices**, zero data loss. Removed: 2015/2020 import generations (merged fields + re-parented PDFs), inari↔numenpc cross-server duplicates, 5 residual + a 2-volume work split into 2 notices. 26 multi-version groups (preprint/article, translations) linked as Zotero *Related* (53 notices). Collections `CIRED`/`LEESU` converted to **tags** and deleted; only `!! Documents à consulter` (686) remains. Scripts in `src/`: `reconcile_zotero`, `zotero_dedup`, `zotero_relate`, `zotero_tag_collections`. Backups in `outputs/zotero_backup_*.json` (gitignored).

**0015 (Antonin's recueil) — was blocked, now resolved:** group `Recueil_CIRED` = the "recueil 50 ans CIRED" curated by **Antonin** (separate inari tree `Wehurei6-recueil_50ans_CIRED/`, own `YYYY-NN` numbering). It does NOT cleanly join My Library — only 50/131 matchable (id+hash+title/author/year union), 81 unjoinable (files outside local archive; Antonin's title corrections break title matching). Antonin has no mapping table (confirmed). The original "import his corrections" plan was stuck without that table. **Unblocked 2026-06-23:** 0015 became a tracker split into 0018 (ingest genuinely-new docs, keyed on the file's `YYYY-NNN`) + 0019 (propagate corrections via fuzzy match + human review), and the group was **mirrored into collection VPDB49CK** rather than joined by table. Full live state and the deletion gate: see [[project_recueil_merge]].

**How to apply:** Don't plan HAL-related work unless reintroduced. Don't plan a bulk RIS import — the catalogue exists and is now deduplicated. Match Zotero records by **identifier (CIR_/ENPC/docid), never by title** — the Sachs fonds reuses titles across distinct works. Dedup invariant: re-parent the PDF onto the master BEFORE deleting a twin. `--apply` on every Zotero-writing script requires `--backup`. Zotero auto-creates the reciprocal `Related` link.

Related closed tickets: 0003 (HAL check), 0005 (HAL batch) — superseded/deferred. 0013/0014/0016/0017 — dedup/tags/relate, done. **0008 (reconciliation) closed (PR #9, 2026-06-23)** — its keyless-doc matcher is `src/match_untyped.py`. Tracker 0015 stays open (children 0018/0019); enrichment swarms 0021–0024 spun off.
