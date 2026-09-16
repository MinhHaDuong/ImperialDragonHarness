---
name: reference-what-consumes-sdt-in-zotero-10
description: In Zotero 10.0.2 only the reader consumes SDT packs; search and full-text indexing do not touch them.
metadata: 
  node_type: memory
  type: reference
  originSessionId: f7d7cc4a-5b20-40a1-9710-3d81ce55aa58
  modified: 2026-09-14T10:44:25.801Z
---

Measured 2026-09-14 by unpacking `app/omni.ja` from the shipped 10.0.2 build.

**Exactly two files reference `Zotero.SDT`**: `chrome/content/zotero/xpcom/sdt.js`
(the service) and `chrome/content/zotero/xpcom/reader.js` (the only caller).
`reader.js` hands the reader a `getSDTPack` callback and pulls **at reader init**.
Zotero's own comment: *"so the pack is ready when a feature needs it, and a reader
build without SDT support never triggers extraction."*

**Search does not use SDT. Full-text indexing does not use SDT.** The only mention
in `fulltext.js` is a comment warning not to delete the SDT cache while cleaning
the storage directory.

`Zotero.SDT` exposes three methods — `getPack`, `ensure`, `getReader` — all
read-or-generate. **There is no import path**: you cannot hand Zotero a pack you
produced yourself, however good it is (this kills "use my Grobid TEI instead").

Why it matters: the natural assumption is that preparing packs speeds up *search*.
Today it speeds up *opening a document*. The search case is prospective — that is
what Zotero PR #6012 is about — so any claim in [[project-sitter-release-state]]
or user-facing prose must hedge it. The sitter's release notes say "may … someday",
which is correct and was checked.

Extraction engine, same measurement: PDF.js `getTextContent()` plus a learned
layout stage — two ONNX models (~4.2 MB classifier, ~4.2 MB clusterer, 350 KB
repair) running in WASM (`ort-wasm-simd-threaded.wasm`, **no WebGPU provider**, so
CPU only). **No OCR anywhere**: no Tesseract in the app, and all four "OCR"
mentions are about tolerating text someone else OCRed. A scan with no text layer
yields nothing.
