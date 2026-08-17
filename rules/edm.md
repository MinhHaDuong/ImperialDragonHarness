<!-- last-reviewed: 2026-08-14 -->
# Electronic document management (EDM)

Discipline for source documents and bibliography across writing and research
projects. Zotero is the system of record; git holds neither the sources nor the
`.bib`.

- **Zotero is the system of record** for source documents and bibliography.
  Every source — PDF, HTML snapshot, or the author's own research notes — lives
  there with the correct item type, real author/date/pagination, and the file
  attached.
- **`docs/` is staging, not a home.** Source documents *and* the author's own
  `*.md` research notes are staged in a project-local `docs/`, then stored in
  Zotero. `docs/` is git-ignored in full (`*.pdf`, `*.html`, `*.md`) — never
  tracked. Neither binaries nor notes belong in the repo.
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
- **A text layer sometimes drops the mathematics, silently.** Two of four
  facsimiles in one corpus rendered the prose in full and zero displayed
  equations (2026-08-17), and the extraction reads fluently either way. So
  when a claim turns on formal content, count the lines carrying `=` in the
  pages at issue; prose without equations is the failing case, and then you
  render the page (`pdftoppm -png -scale-to 1500`) and read it. A grep cannot
  find a formula that was never extracted, so a nil result is not a negative
  finding.
- **Project `.bib` files are also staging**, git-ignored, synced to Zotero. The
  `.bib` is provenance scaffolding, not the source of truth.
- **Periodic sync + purge.** Reconcile staging to Zotero periodically (correct
  item type, scraped metadata, file attachment), and **purge staging on
  archival after publication** — Zotero retains everything.
- **Reports carry a page count** — pass `numPages` on the entry. The Zotero
  `report` type has no `numPages` field, so `zotero-import` files it in Extra
  as the CSL variable `number-of-pages`; that is the correct home, not a
  fallback.

Why: git repos stay lean (no binary bloat, no report PDFs in history) and
durable provenance is centralized in Zotero, where it persists and syncs.
Staging is transient by design.

Two skills implement this workflow: `zotero-import` (PDFs) and `index-source`
(URLs) — fetch → stage in `docs/` → archive in Zotero (RIS + attachment) →
record the citation.

This rule governs *source documents and bibliography staging*. It does not
touch [git.md](./git.md)'s "commit handoff artifacts" rule: generated files a
downstream workpackage consumes (figures, tables, `\input`ed macros) are
durable state and stay tracked. No contradiction — different object classes.
