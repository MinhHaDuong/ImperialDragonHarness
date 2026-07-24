---
name: libreoffice-headless-pdf-export
description: "`soffice --headless --convert-to pdf file.docx` is a clean retirement path for WeasyPrint when DOCX is the source of truth — diacritics, italics, monospace blocks all survive"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff1f28d7-df07-4e2e-8181-0eb5c4a6e448
---

For a manuscript pipeline where DOCX is the editor-facing source of truth,
LibreOffice headless can derive the PDF in one command — no Python deps, no
LaTeX install, no font hassles for Vietnamese diacritics:

```bash
soffice --headless --convert-to pdf main.docx
```

**Why**: Verified on chemin-de-voix prototype (LibreOffice 24.2.7.2 on padme):
multilingual French + English + Vietnamese-with-diacritics + GAMS code block
in monospace all rendered correctly in a 99 KB PDF. The `--print-pdf` variant
of the WeasyPrint+HTML pipeline becomes redundant once DOCX is the canonical
artifact, and one tool replaces a Python dependency.

**How to apply**: When choosing a PDF rendering path for a DOCX-source
project, default to `soffice --convert-to pdf` unless you specifically need
fine LaTeX-grade typography (which Pandoc/xelatex would provide, at the cost
of an entire TeX install). Reference `make pdf` target in ticket 0252.
