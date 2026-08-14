<!-- last-reviewed: 2026-08-14 -->
# Book

Document-type conventions only — language norms live in `lang/`, universal
prose in `prose/_all.md`.

- **Terminology is consistent across chapters**: one concept, one term, book-wide — no local synonyms per chapter.
- **Chapters open with what the reader gets and close on the point**, not on a summary of what was said.
- **Cross-reference by label** (`\ref`/`@ref`), never by hard-coded chapter/page number; page-relative wording ("as seen above") breaks under reflow.
- **Notation is introduced once, in one place**, and reused; a notation table beats re-explaining symbols per chapter.
- **Each chapter's dependencies are explicit**: say early which prior chapters it builds on, so selective readers can route.
- **Front matter promises only what the body delivers** — keep the preface's roadmap in sync with the actual chapters.
