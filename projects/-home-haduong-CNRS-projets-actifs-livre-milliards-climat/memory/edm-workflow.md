---
name: edm-workflow
description: "User's EDM workflow (cross-project) — docs/ and .bib are staging; Zotero is the system of record; docs/ synced to Zotero and purged on archival after publication."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7796be7-c37c-43f6-8702-99dbdd355e78
---

The user's electronic document management (EDM) discipline, applicable across
writing/research projects (harness-level, not specific to one book):

- **Zotero is the system of record** for source documents and bibliography.
- **`docs/` is staging, not a home.** Source documents *and the author's own
  research notes* (`docs/*.md`) are *staged* in project-local `docs/`, then
  *stored in Zotero* (with correct item type + scraped metadata + attachment).
  `docs/` is git-ignored in full (`*.pdf` / `*.html` / `*.md`) — never tracked
  (neither binaries nor notes belong in the repo; Zotero holds them).
- **Periodic sync + purge.** `docs/` is periodically checked/synced to Zotero,
  and **purged on archival after publication** — Zotero retains the documents.
- **Project `.bib` files are also staging**, to be synced to Zotero. The `.bib`
  is provenance scaffolding, not the source of truth.

**Why:** keeps git repos lean (no binary bloat, no 13 MB report PDFs in history),
and centralizes durable provenance in Zotero where it persists and syncs. Staging
areas are transient by design.

**How to apply:** when indexing a source — fetch → stage the document in `docs/`
→ archive in Zotero (RIS + `L1` attachment, correct type, real author/date/
pagination) → record the citation. Gitignore `docs/*.pdf` / `docs/*.html`. Treat
`docs/` and `.bib` as ephemeral; reconcile to Zotero. On publication, purge
`docs/`. Reports carry a page count in metadata. See [[verifier-dans-le-vrai-lieu]].
