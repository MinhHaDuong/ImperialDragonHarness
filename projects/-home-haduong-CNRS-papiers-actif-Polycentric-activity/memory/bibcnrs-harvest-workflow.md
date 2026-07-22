---
name: bibcnrs-harvest-workflow
description: "Working pattern for building a full-text bibliography — agent horde for OA, then bibCNRS manual harvest watched via inotify on ~/Downloads"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c33ff214-23dc-4f45-835b-03e43303a547
---

Pattern validated 2026-07-03 for the P1 bibliography (96 entries, 100% full-text coverage in one day).

**Why:** Agents can only fetch legal open-access copies (arXiv, HAL, author pages, Cowles/NBER/RAND, public-domain scans); paywalled items need the user's bibCNRS access (Click & Read browser plugin) or personal copies, which no agent can drive.

**How to apply:**
1. Horde pass: one fetch agent per reference; instruct to grep the source notes first to disambiguate vague citations ("KRS 2002"), never Sci-Hub/LibGen, verify PDF magic bytes + first-page content, return a ready biblatex entry.
2. Second wp-hunt pass with specific leads pays off: Rockafellar's UW page hosts his out-of-print books; INRIA RRs are on HAL; Cowles reprints its old papers; RAND classics are free; check copyright expiry for pre-1953 authors.
3. For the remainder: serve the user a local HTML page of clickable https://doi.org/ links (Click & Read reroutes via bibCNRS), then arm `inotifywait -m -e close_write -e moved_to` on ~/Downloads filtered to .pdf; identify each arrival by `pdftotext -l 1`, rename to `<BibKey>-<Author><Year>.pdf`, move to docs/.
4. Verify everything: file fields ↔ docs/ bijection (no missing, no orphans), magic bytes, title-words-in-first-3-pages match with visual check (pdftoppm + Read) for scans without text layer; `biber --tool` for syntax. The verification catches real errors — it found a wrong title (Afriat) and a wrong volume (Heckscher 1916 is Årg. 18 not 17, per the JSTOR cover page).

Gotchas: Firefox downloads arrive as temp names then rename (watch moved_to); ISTEX serves ark__* filenames; user-supplied files may be 0-byte failed downloads — always check size; qpdf (snap) cannot read ~/.claude paths, use gs; project docs/ may be gitignored deliberately (copyrighted PDFs) — commit only refs.bib.
