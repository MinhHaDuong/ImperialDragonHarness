---
name: reference-cited-works-local-docs-articles
description: "Project rule — every cited work's PDF must be available locally in docs/articles/ (gitignored); moved to Zotero at publication"
metadata: 
  node_type: memory
  type: reference
  originSessionId: abeb176f-22ca-461f-bb52-7bdffd08f43b
---

Author rule (2026-07-08): **everything cited in the manuscript must be available locally as a PDF in `docs/articles/`**, then moved into Zotero at publication time.

- `docs/articles/` is the project's local reference library — it already holds the manuscript's cited works (Espeland & Stevens, Gieryn, Star & Griesemer, Negishi, Nordhaus, Manne & Richels, Weitzman, Michaelowa, Caruso & Ellis, Jachnik, Stadelmann, etc.).
- **Gitignored** (`docs/*.pdf` and `docs/articles/*.pdf` are not committed) — local availability only, not repo state. The committed artifact is the bib entry in `content/bibliography/main.bib`.
- Naming: bibkey-style (`michaelowa2007.pdf`, `caruso_ellis2013.pdf`) or `Author Year - Title.pdf`; for author-supplied works I used `<bibkey>-<short-title>.pdf`.
- Workflow when adding a citation: author downloads the source → verify metadata **sur pièce** (read the PDF's copyright page / EPUB OPF, no fabrication) → add the bib entry → drop the PDF in `docs/articles/`. Prefer PDF over EPUB (Read tool can't open EPUB).
- The **decision of which works to cite where** (and replace-vs-complement existing refs) stays the author's, made on the actual documents. See [[project_oeconomia_rr_pipeline]] and [[feedback_manuscript_number_provenance]].
