---
name: zotero-10-plugin-and-reindex
description: "Zotero 10 facts learned building the full-text control plugin — manifest needs update_url, group libraries load lazily (use the async getter), no bulk reindex button, extraction speed 60–80 pages/s, the plugin's endpoints and client."
metadata: 
  node_type: memory
  type: reference
  originSessionId: b7159928-959f-4103-8860-e2c11cdefc7a
  modified: 2026-09-02T15:47:09.869Z
---

Zotero 10.0.1, the author's build, 2026-09-02:

- **Plugin manifest**: `applications.zotero.update_url` is mandatory (loader
  error "update_url not provided"); `browser_specific_settings` rides beside
  `applications`; `strict_max_version` "10.*" accepted. An `updates.json`
  with an empty `updates` list satisfies the check. Build the .xpi OUTSIDE
  bench/ (the bench guards read every file under bench/ as text).
- **Endpoints**: constructor functions on `Zotero.Server.Endpoints` (the
  server does `new endpoint`), `init({method, pathname, searchParams,
  headers, data})` returning `[status, contentType, body]` or a promise.
- **Group libraries load lazily after a restart**: `Zotero.Items.getByLibraryAndKey`
  throws on an unloaded library (every group-key call returned 500);
  `getByLibraryAndKeyAsync` loads on demand.
- **No bulk reindex in the GUI** since Zotero 7's successors: Settings →
  Advanced → Search has the two limits and an Index Statistics box with a
  progress bar; "Index Unindexed Items" skips partial ones. Per item: the
  reindex glyph in the attachment pane. `Zotero.FullText.indexItems(ids,
  {complete: true})` ignores the limits.
- **The local API's fulltext endpoint** returns `indexedPages`/`totalPages`
  beside the text, and accepts PUT (428 without `If-Unmodified-Since-Version`).
  Group items answer under `/api/groups/<id>/…`, not `/api/users/0/…` (404).
- **Extraction speed**: 60–80 pages/s end to end; 2 913 pages in 46 s. A run
  showing hours with no cache written is stuck, not slow — restart Zotero.
- **Reindexed group attachments come back at full-text version 0**; user
  library ones take fresh versions (X6's class, ticket 0025).
- Tool: `bench/zotero-fulltext-plugin/` + `bench/zotero_fulltext.py`
  (`status KEY…`, `reindex KEY… --wait`), merged PRs #189/#199.
  Related: [[fork-cwd-and-worktree-guard]].
