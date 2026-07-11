---
name: Bibliography toolchain
description: User uses biblatex+biber (not BibTeX), Zotero as canonical library, local .bib files are staging
type: user
---

Uses **biblatex** compiled with **biber**, not classic BibTeX.

Canonical reference library is **Zotero** (v9+ as of April 2026, fast release cycle).
Local `.bib` files in repos are staging areas — not the source of truth.

Workflow: at manuscript submission, import approved `.bib` entries into Zotero
(File → Import) with fulltext PDFs. Not before (citations churn during drafting),
not after publication (you've moved on).

Reference `.bib` for formatting conventions: `~/CNRS/html/src/Ha-Duong.bib`.
Key style: `Author-NameYEAR:slug`. Biblatex fields: `date`, `journaltitle`,
`eprint` + `eprinttype` for HAL/arXiv.
