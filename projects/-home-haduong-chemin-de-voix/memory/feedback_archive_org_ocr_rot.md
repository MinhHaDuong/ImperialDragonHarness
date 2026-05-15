---
name: feedback-archive-org-ocr-rot
description: "archive.org / Anna's Archive scan-derived sources (TXT, HTML \"Full text of\", DjVu) are often OCR-rotted; prefer Wikisource / Gutenberg / Gallica clean transcriptions and refetch rather than salvage."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 73828333-04df-4434-9a2c-e4eb6149a691
---

archive.org and Anna's Archive sources that derive from scanned books (DjVu OCR, "Full text of X" HTML wrappers, scanned PDFs without text layers) are frequently OCR-rotted to a degree that defeats LLM cleaning. Prefer a clean digital edition from Wikisource, Project Gutenberg, or Gallica. If a clean source exists, **refetch** — don't salvage with custom regex; effort dwarfs yield.

**Why:** This session hit the same pattern five times in one project:
- voix-heloise: archive.org 8ZSUP191 `.txt` → garbled OCR → 7 UNCOVERED chunks → deleted, kept clean Wikisource version
- voix-rahan: `e3ce5a84c11f.pdf` scanned PDF → `W> ■ * ,}%&? ffî` noise → ticket 0132 to refetch from Wikisource Édition Albert Savine 1888
- voix-hcm: `Full text of _Prison Diary_.html` (FLPH 1972 scan) → `FOREIQN I^ANGIIAOES PUBLISHING- HOUSH` → purged
- voix-hcm: `HoChiMinh-PrisonDiary-2ndEd-Hanoi-1965.pdf` → image-only, 0/54 pages have text layer → purged
- voix-hcm: `hochiminhtestament_djvu.txt` → archive.org DjVu OCR → ticket 0133 covers refetch

Custom regex archaeology for these always loses to a 30-second `https://fr.wikisource.org/wiki/<work>` URL check.

**How to apply:**

1. **Diagnostic signals of scan-OCR rot** (any one is enough to suspect):
   - Letter substitutions: `Q` for `G`, `I^` for `L`, `1` for `l`, `0` for `O`
   - Word-boundary loss: missing spaces between words; words split across line breaks
   - Scattered single-character lines or runs of punctuation/symbols
   - File extension is `_djvu.txt` or filename contains "Full text of"
   - PDF source has zero text layer (`pypdf` extracts empty string from every page)
   - File came from `archive.org/details/...` or Anna's Archive

2. **Before salvage, check for a clean digital edition:**
   - Wikisource in the work's original language (`fr.wikisource.org`, `en.wikisource.org`, `vi.wikisource.org`, `zh.wikisource.org`, `la.wikisource.org`)
   - Project Gutenberg
   - Gallica (BnF) — for French canonical editions
   - The work's modern reprint distributor (rarely free, but often clean)

3. **Disposition decision tree:**
   - Clean edition exists → **refetch** (cheap, high yield)
   - No clean edition, editorial value low → **reject** (mark `rejected: ocr-rot` in inventory, remove chunks)
   - No clean edition, editorial value high → escalate; salvage only if a domain expert can validate the fragments

Related: [[feedback_coauthored_rejection]] (similar "noise pollutes the voice signal" reasoning); ticket 0132 (rahan Xipéhuz refetch), 0133 (voix-hcm VN gap).
