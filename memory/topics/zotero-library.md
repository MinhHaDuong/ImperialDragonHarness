# Zotero library

Scope: Web API access to the author's Zotero library — identifiers, endpoints
and access conditions — and the harness's Zotero interface design. A scoped reference note, not a factual capture: what
follows is the note's content, still attributed to it.

## Supported observations

The source note records the library's user identifier and username, the API
item and file-download endpoints, the key locations and their read/write
scopes, and the main collection used for Vietnamese energy policy decisions.
It also records one access asymmetry, measured 2026-09-07 on two groups: group
file downloads require a key — an anonymous probe gets 404 where a member gets
the bytes — so an anonymous probe cannot distinguish "no bytes on the server"
from "not allowed to read them".

## Interface architecture (2026-10-02 to 2026-10-04)

Dated design, superseded for `scripts/zotero.py` by the 2026-10-15/16
decisions below. The author agreed a design in which each skill chooses its transport, with
hard invariants (no sqlite writes, client-side merges, backup then dry-run
then apply); the rule file became `rules/zotero.md` and the EDM acronym was
retired (PR #1143). The web survey of that date recorded that Zotero 10 made
the local HTTP API writable; it is dated, perishable evidence kept in
`conception/zotero-integration.md` Annex A. Semantic retrieval belongs to the
author's separate search-works-for-zotero project. The overnight train then
consolidated one `zotero` skill over a `scripts/zotero.py` backend (tickets
1018, 1025, 1026). Duplicate merges remain a client-side author action. The
safety contract did not cover every verb identically: `attach` created with
`If-None-Match: *` and the version guard existed only in `enrich`, as the
#1179 review established (verbs since renamed; not re-verified on current code).

## Refresh: local API preference and on-demand reconciliation

The [2026-10-14 author preference](../journal/2026/2026-10-14-zotero-local-api-preference.md)
is explicit: « N’hésite pas à demander que j’ouvre le Zotero local pour passer
par l’API, ça va plus vite. » Availability still needs checking; this changes
neither deduplication nor the prohibition on SQLite writes.

The [2026-10-15 reconciliation episode](../journal/2026/2026-10-15-molt-zotero-reconcile-removed.md)
records a zero-staged-file run killed after 300 s without a report. Cache bytes
were unchanged and no project had an apply opt-in; the slow rebuild's cause
was not established. The author chose removal from Molt and on-demand Zotero
reconcile, with an early exit before index loading for empty staging (#1434).
Review minors became 1111/1112. Subsequent merged #1437 repaired empty reports
and apply preflight (Git source evidence at this pass's base); 1112/1113 remain
separate follow-ups. Removing a housekeeping step does not withdraw
`rules/zotero.md`'s reconciliation discipline or prove library completeness.

## Refresh: local-only helper (2026-10-15 to 2026-10-16)

Author decisions, in order ([local-only](../journal/2026/2026-10-16-zotero-local-only-decisions.md),
[pyzotero](../journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md),
[verbs](../journal/2026/2026-10-16-zotero-verbs-exact-match.md)):

- 2026-10-15 (1113/1111): `scripts/zotero.py` works only locally and is
  stateless: no Web API, no local index, no cache; edits to existing items are
  reported, not applied.
- 2026-10-16 (PR #1441), after a first version read `zotero.sqlite` and fell
  back to a lagging snapshot while Zotero ran: "API ONLY, NEVER SQLITE". Reads
  go through the local API; if Zotero is down the helper tries to launch it and
  otherwise does nothing.
- Same day: "Plan A. On arrête le YAGNI massacre": pyzotero 1.16 in local mode
  replaced the hand-rolled client and the desktop-connector write path, and "In
  tests up Zotero as a fixture or skip -- no mock" removed the stub.
- PRs #1447/#1448 (1116): subcommands renamed without aliases; `probe` split
  into `extract-metadata` and `find-work` ("Extracting is different than looking
  up."); matching is exact normalised identifier or PDF md5 only, title hits are
  candidates; `check-staging` merges audit and reconcile.
- 1112 (PR #1440): `/lair` proposes a staging reconcile when a `docs/` file
  changed that day, never runs it automatically.

Observations. Zotero's `server_localAPI.js` has no write methods at tag 9.0.6
and has them from 10.0.0 to 10.0.6, confirming the earlier survey. The live test
fixture first passed the author's DISPLAY to the throwaway Zotero and opened
windows on the author's screen; it now runs on a private Xvfb, and shared `/tmp`
full of other sessions' files once stopped Xvfb. A review seat opened the real
`zotero.sqlite` read-only and changed only the `-shm` mtime; the next round used
`immutable=1`. A worker's report claimed an author choice the author had not
made; the orchestrator asked. pdf2doi returned a DOI from a reference list and
was rejected. The two entries give different pre-change line counts for the
helper (3,177 and 3,100), unreconciled.

## Sources and exceptions

- [Préférence explicite pour l’API locale, 2026-10-14](../journal/2026/2026-10-14-zotero-local-api-preference.md) — l’utilisateur accepte qu’on lui demande d’ouvrir Zotero pour utiliser son API et gagner du temps.

- [Zotero library](../reference_zotero.md) — scoped reference note, interpreted; no episode reconstructed.
- [Zotero architecture session, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Zotero train raid](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
