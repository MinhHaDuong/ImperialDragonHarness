---
paths:
  - "**/*.bib"
  - "**/*.ris"
  - "**/docs/**"
  - "**/wiki/works/*.qmd"
  - "**/wiki/references/*.qmd"
  - "**/reading-notes/**"
last-reviewed: 2026-11-11
---
# Zotero management

Loaded when you touch a bibliography, a staging directory or a reading-note
draft. The other half of
its trigger is a task, which no glob reaches: the zotero skill names this file, and a
session doing Zotero management by hand
should read it.

Discipline for source documents and bibliography across writing and research
projects. Zotero is the record for works and reading notes; repositories hold
drafts under review and generated snapshots. Project bibliographies may be
tracked in git; source documents stay outside it.

- **Zotero is the record for works and reading notes.** Every source — PDF,
  HTML snapshot — lives there with the correct item type, real
  author/date/pagination, and the file attached. A reading note is an HTML
  child note under its work's item, not a standalone Document. A repository
  holds only a draft under review (on a branch, until merged) and generated
  snapshots of published notes; after merge the draft is published to Zotero
  through the local API only, and Zotero's note is authoritative.
  A Document with a stored `.md` attachment filed before this rule stays as it
  is; a re-filed note supersedes it (reading-note skill § 4).
- **`docs/` is staging, not a home.** Source documents (including PDFs, HTML snapshots, and OCR output) *and* the author's own
  `*.md` research material are staged in a project-local `docs/`, then stored in
  Zotero. `docs/` is git-ignored in full (`*.pdf`, `*.html`, `*.md`) — never
  tracked. Binaries never belong in the repo; reading-note drafts live outside
  `docs/`, where review can see them.
- **Check `docs/` staging *and* Zotero before declaring a source
  inaccessible.** A source-verification agent lists `docs/` (author-name
  variants included) and queries the Zotero library before any web search,
  and every "remained inaccessible" sentence in a note is re-read against
  both. For a paywalled work, also query ISTEX (national-licence full text,
  token in `~/.config/keys/istex.env`) before concluding "institutional
  access required" — the full chain is docs/ → Zotero → ISTEX → open web →
  author. Coverage varies by publisher (JRSS-B only from 1997; Elsevier
  serves native full text through at least 2016). A scan without a text
  layer is not inaccessible — `ocrmypdf` is installed. (Eight false
  "inaccessible" verdicts in one session, HET 2026-08-10, including a fake
  showstopper and three fictitious "human action required" items; ISTEX
  validated both ways on 2026-08-11 — honest negative on Smith 1961,
  instant fulltext on Shiozawa 2016.)
- **A cited page number is read on the page, never interpolated from an
  extraction.** Keeping the fulltext locally is worth little if the locator is
  guessed. `pdftotext` over a whole document concatenates body, footnotes,
  headers, and running feet in an order that is not the layout's, so position
  in the flow is not proportional to the printed folio: citing p. 262 because
  the sentence sat around line 290 of a 16-page extract put the reference two
  pages off the truth, which was p. 260 (HET, Karush footnote, 2026-08-14).
  Extract the single page (`pdftotext -f N -l N`) and read the folio it
  carries, or render it and look. Two cheap cross-checks: the running foot
  often prints the article's official page range (it corrected a bibliographic
  range in the same pass), and the first page of the *next* chapter bounds the
  previous one (chapter XX opening at p. 330 confirmed Gale–Kuhn–Tucker at
  pp. 317–329). A plausible wrong locator is the costly failure — a referee who
  opens the page and finds nothing stops trusting the whole apparatus.
- **A text layer sometimes drops the mathematics, silently.** A facsimile can
  render its prose in full and carry none of its displayed equations, and the
  extraction reads fluently either way. So when a claim turns on formal
  content, count the lines carrying `=` in the pages at issue; prose without
  equations is the failing case, and then you render the page
  (`pdftoppm -png -scale-to 1500`) and read it. A grep cannot find a formula
  that was never extracted, so a nil result is not a negative finding.
- **Project `.bib` files may be tracked.** Zotero remains authoritative for
  bibliographic metadata; keep the project bibliography aligned with it.
  Project-owned citekeys and annotations may stay in the `.bib`. Each cited
  entry carries a reader route: a DOI or an open-access or archived URL.
  A `file=` field is a local hint, not the reference or a portable reader
  route. The cited-works-availability test still checks local fulltexts
  (`prose-adherence-tests.md`).
- **Periodic sync + purge.** Reconcile source-document staging to Zotero (correct item type,
  scraped metadata, file attachment) and **purge staging on archival after
  publication** — Zotero retains everything. The reconcile is run by the author
  on demand (`/zotero check-staging`) and is *proposed* by lair, never run
  automatically: when the project has a `docs/` directory and a file under it
  has an mtime since the start of the current day, lair's final summary offers
  it (`skills/lair/zotero-reconcile-trigger`, a cheap mtime scan with no Zotero
  access and no network); otherwise lair is silent. Molt does not run it.
- **Reports carry a page count** — pass `numPages` on the entry. The Zotero
  `report` type has no `numPages` field, so the `zotero` skill's import flow files it in Extra
  as the CSL variable `number-of-pages`; that is the correct home, not a
  fallback.

Why: git repos stay lean (no binary bloat, no report PDFs in history) and
durable provenance is centralized in Zotero, where it persists and syncs.
Source-document staging is transient by design; a tracked bibliography and
reading-note drafts under review remain with the project.

One skill implements this workflow: `zotero` (verbs as arguments, PDF and URL
intake alike) — fetch → stage in `docs/` → archive in Zotero (the item and
its attachment, created through the local API) → record the citation. A
fetcher (`doifetch.sh --doi/--isbn`, `probe-url.py`) leaves its receipt, the JSON line it
prints, in `docs/.receipts.jsonl`; `check-staging` and `find-work` read it.

This rule governs *source documents, reading notes and project bibliographies*. It does not
touch [prose/workpackages.md](./prose/workpackages.md)'s "Don't gitignore handoff artifacts" rule: generated files a
downstream workpackage consumes (figures, tables, `\input`ed macros) are
durable state and stay tracked. No contradiction — different object classes.
