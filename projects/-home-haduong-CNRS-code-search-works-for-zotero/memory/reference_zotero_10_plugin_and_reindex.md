---
name: zotero-10-plugin-and-reindex
description: "Zotero 10 facts learned building the full-text control plugin — manifest needs update_url, group libraries load lazily (use the async getter), no bulk reindex button, extraction speed 60–80 pages/s, the plugin's endpoints and client, and how to read document-worker version drift the changelog won't tell you."
metadata: 
  node_type: memory
  type: reference
  originSessionId: b7159928-959f-4103-8860-e2c11cdefc7a
  modified: 2026-09-11T16:24:39.890Z
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
- **Extraction speed, flat path**: 60–80 pages/s end to end; 2 913 pages in 46 s.
  Re-measured 2026-09-03 on the **same** document, two reps: **62,6 s and 64,9 s**
  (45,7 pages/s). Same tool, same key, 37 % apart from the 46 s reading — cause
  not isolated (machine load, poll quantum, and a build change are all live
  candidates; the 2026-09-03 reps ran with several sessions active). Quote the
  range, not either endpoint, and re-measure on an idle machine before treating
  it as pinned. Measure with `reindex … --wait --poll 0.25`, and read the **outer
  wall**: `complete()` is ledger-state based, so on an already-complete item it
  reports "1 of 1 complete" at 0 s while the parse runs on — only `busy` tracks
  the job. A run showing hours with no cache written is stuck, not slow — restart.
- **Extraction speed, SDT path** (`.zotero-sdt-cache`, the ONNX document-worker):
  **5,26 pages/s** on the 2 913-page volume, and 5–9 pages/s across a hundredfold
  size range — roughly **9x slower than the flat parse** and 42x `pdftotext`
  (219 pages/s on the same file). ~24,6 h to pack a 464 599-page library. Packs
  are produced only for attachments opened in the reader, and the worker is
  **uncapped** where the flat path honours `pdfMaxPages`. Timings come from each
  pack's `dateCreated` → mtime, so they are upper bounds. See
  `verification/EXTRACTION-ROUTES.md`.
- **Reindexed group attachments come back at full-text version 0**; user
  library ones take fresh versions (X6's class, ticket 0025).
- Tool: `bench/zotero-fulltext-plugin/` + `bench/zotero_fulltext.py`
  (`status KEY…`, `reindex KEY… --wait`), merged PRs #189/#199.
  Related: [[fork-cwd-and-worktree-guard]].
- **Zotero 10.0.2, 2026-09-11: the client changelog does not cover the
  document-worker submodule.** `zotero.org/support/changelog` for 10.0.1/10.0.2
  named only reader/Read-Aloud/full-text-*statistics* fixes — silence there is
  not evidence the SDT extractor didn't change. To check, read the shipped
  build's own stamps directly: `python3 -c "import zipfile,json;
  z=zipfile.ZipFile('/opt/zotero7/app/omni.ja');
  print(z.read('resource/document-worker/metadata.json').decode())"` (path is
  per-install; find with `find / -name omni.ja` under the app dir, not the
  profile). Between the 10.0 build (`20260817151751`, 2026-08-17) and 10.0.2
  (`20260909184950`, 2026-09-11), `SDT_SCHEMA_VERSION` moved 1.1.0→1.2.0 and
  `SDT_PROCESSOR_VERSIONS.pdf` moved 3→14 — neither `zotero/document-worker`
  nor `zotero/structured-document-text` publishes release notes, so this is
  the only way to see it. Update history/build IDs live in
  `<profile>/updates.xml` and `<app>/updates/last-update.log`.
- **`Zotero.SDT.ensure()` blocks on a stale-processor pack; `getPack()` does
  not.** Per `zotero/zotero#6012`'s pinned `test/tests/sdtTest.js`
  (`19e79625b1c6fbbdd75367aa85b62d5a7080d7f6`): `getPack()` returns the old
  pack immediately and regenerates in the background, but `ensure()` — the
  call an eager scheduler like the sitter's census makes — waits for the
  fresh pack before resolving. So a `SDT_PROCESSOR_VERSIONS` bump costs a
  synchronous, library-wide pass through every `ensure()` caller, recurring at
  whatever cadence upstream ships it (observed: two point releases moved the
  PDF processor 11 steps with zero announcement). Full finding:
  ticket 0754's 2026-09-11 log entry, `search-works-for-zotero` PR #519.
- **Scripting a real "Install Add-on From File" without a human click, and
  the wrong API that looks right.** The Firefox RDP `AddonsActor`'s only
  install method is `installTemporaryAddon()` -- Firefox's non-persistent
  "Load Temporary Add-on" path (about:debugging), which does not exercise
  `extensions.json` the way a real install does and cannot be substituted
  for one. The real call, read verbatim from Zotero's own shipped
  `omni.ja` (`toolkit/chrome/toolkit/content/mozapps/extensions/
  aboutaddonsCommon.js`, `installAddonsFromFilePicker()`):
  `AddonManager.getInstallForFile(file, null, {source: "about:addons",
  method: "install-from-file"})` then `AddonManager
  .installAddonFromAOMWithOptions(browser, uri, install,
  {preferUpdateOverInstall: true})` -- `browser`/`uri` are only threaded
  into inert observer-notification payloads in this build, never
  dereferenced, so `null`/a throwaway URI is safe. Reachable over RDP by
  attaching to the chrome/parent-process target's generic eval actor, not
  the add-ons actor. Arming the debugger server needs no restart: replay
  `handleDevToolsServerFlag()`'s five statements via Tools -> Developer ->
  Run JavaScript (full chrome privilege there already), or seed
  `devtools.debugger.remote-enabled`/`devtools.chrome.enabled` into a
  fresh profile's `prefs.js` before first launch. One more pref matters and
  is easy to miss reading source alone: `devtools.debugger.prompt-connection`
  (true by default) blocks the connection on a server-side "allow?" prompt
  before the hello packet -- in unattended/headless use this hangs forever
  with zero bytes received, not a clean error; set it `false`. Built and
  proven (read-only, and on a throwaway profile a real 17-cycle
  install/disable/enable run) as `bench/zotero_rdp_client.py` +
  `bench/sitter_volume_experiment.py`, ticket 0766, `search-works-for-zotero`
  PR #523/#526, 2026-09-11.
