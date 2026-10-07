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

The author agreed a design in which each skill chooses its transport, with
hard invariants (no sqlite writes, client-side merges, backup then dry-run
then apply); the rule file became `rules/zotero.md` and the EDM acronym was
retired (PR #1143). The web survey of that date recorded that Zotero 10 made
the local HTTP API writable; it is dated, perishable evidence kept in
`docs/zotero-integration.md` Annex A. Semantic retrieval belongs to the
author's separate search-works-for-zotero project. The overnight train then
consolidated one `zotero` skill over a `scripts/zotero.py` backend (tickets
1018, 1025, 1026). Duplicate merges remain a client-side author action. The
safety contract does not cover every verb identically: `attach` creates with
`If-None-Match: *` and the version guard exists only in `enrich`, as the
#1179 review established.

## Sources and exceptions

- [Zotero library](../reference_zotero.md) — scoped reference note, interpreted; no episode reconstructed.
- [Zotero architecture session, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Zotero train raid](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
