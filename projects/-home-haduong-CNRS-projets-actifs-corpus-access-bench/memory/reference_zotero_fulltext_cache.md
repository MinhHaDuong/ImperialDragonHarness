---
name: reference-zotero-fulltext-cache
description: Zotero already extracts PDF text to .zotero-ft-cache — 0.7 GB across 13k attachments here; plus the group-library and Zotero-10 local-API facts
metadata:
  type: reference
---

Zotero extracts a PDF's text on first open and caches it as plain text in
`~/data/Zotero/storage/<ATTACHMENT-KEY>/.zotero-ft-cache`. Measured 2026-08-21:
**13 631 caches, 0.86 GB of text**, median 27 KB, p95 240 KB, max 1.9 MB. 282
are empty and 239 under 2 KB — the no-text-layer population, which is
`ocrmypdf`'s worklist.

Any tool that indexes this library should read those caches rather than
re-extract: it is the difference between minutes and hours (Zoteus builds in
140 s reusing them; ZotSeek quotes ~3 s/paper re-extracting, ≈7.7 h here).
Zotero's own index (`fulltextItems`, `fulltextWords`, `fulltextItemWords` in
`zotero.sqlite`) is word-presence without positions, so it answers "which items
contain these words" and cannot rank or give a page.

Two library facts that bite tools: there are **two libraries** — personal
(9 302 attachments) and the group *ASEAN research collaborative on environment
and development*, id 305258 (7 277 attachments, 5 922 caches). 268 storage dirs
are orphans from deleted items. A tool that only indexes the personal library
silently misses 43% of the extracted text.

**Zotero 10's local API serves group libraries** — `/api/groups/<id>/items`,
`/children`, `/fulltext`, `/collections`, and `/api/users/0/groups` all answer
200 on `127.0.0.1:23119` with no cloud key. That was false before Zotero 10, and
tools still encode the old rule. It also serves `Last-Modified-Version`,
`?since=`, and `?format=versions`; `/deleted` is cloud-only, so deletions need a
key-set reconcile.

Open `zotero.sqlite` read-only while Zotero runs: `file:...?immutable=1`.

Related: [[reference-zotero]], [[project-zoteus-fts5]]
