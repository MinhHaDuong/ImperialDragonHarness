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
