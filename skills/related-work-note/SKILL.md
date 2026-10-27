---
metadata:
  category: research
name: related-work-note
description: "Due-diligence note for one cited paragraph of a manuscript: relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL."
disable-model-invocation: false
user-invocable: true
argument-hint: 'free-form inline — see "Inputs" section'
---

# Related-work due-diligence note

Produce a companion document for a single manuscript paragraph that
gives the author everything needed to defend the paragraph under
peer review.

**Not a systematic review.** The standard is "defensible under peer
review of one paragraph," not exhaustive coverage. Build a search
deep enough that a referee's "why didn't you cite X?" has a
prepared answer.

## Constraints (non-obvious)

- **One paragraph = one note = one invocation.** Re-run freshly
  each time; never recycle an older note. Methods records the
  invocation date as the freshness cutoff.
- **Resolve every identifier before emitting.** WebFetch each DOI
  or URL. Drop or replace entries that don't resolve — never ship
  an unresolved identifier.
- **Check existing refs.bib first.** Reuse existing keys rather
  than minting duplicates. Match the library's key style if clear.
- **One project deliverable.** Output is a single Markdown note; do not
  modify refs.bib or other manuscript files. Source and note intake into
  Zotero, with transient staging and archival receipts, is part of this task.
- **"Related but not cited" is mandatory.** At least two entries
  when alternatives exist. A thin list for a narrow sub-literature
  is fine — say so in Methods rather than padding.
- **No padding.** Every bibliography entry must be directly
  justified. Do not add references for coverage.
- **Non-English titles** must include a bracketed English
  translation: `{Titre original [English translation]}`.

Optional HAL metadata discovery: see [HAL Discovery MCP](../../conception/hal-discovery-mcp.md).
Activate only for this task when supported; direct HAL API remains a fallback.
This pointer does not register or load MCP tools.

## Toolchain

**biblatex** (not BibTeX) compiled with **biber**. Local `.bib` is
staging; the canonical library is **Zotero**. Resolve and import sources at
intake with `/zotero import`, attaching to existing items when needed. Reuse
Zotero identities; the note bibliography is a citation view, not a second
source catalog.

BibTeX template (aligned with `~/CNRS/html/src/Ha-Duong.bib`):

```bibtex
@article{Author-NameYEAR:slug,
  author       = {Author, A. and Author, B.},
  title        = {{Full title}},
  journaltitle = {Venue},
  date         = {YYYY-MM},
  doi          = {10.xxxx/yyyy},
  eprint       = {hal-XXXXXXXX},
  eprinttype   = {hal},
}
```

Keys: `Author-NameYEAR:slug`. Biblatex fields: `date` (not `year`),
`journaltitle` (not `journal`), `eprint` + `eprinttype` for HAL/arXiv.
Omit `url` when `doi` resolves to open-access full text. Keep both
when the DOI gates a paywall and `url` points to an open copy.

## Inputs

1. **Paragraph topic or claim**
2. **Target manuscript path**
3. **Section identifier** (e.g., "§2 Related Work, paragraph 1")
4. **Output path**
5. *(Optional)* **Citation budget**

If any required input is missing, ask once.

## Output template

Seven mandatory sections:

```markdown
---
title: {paragraph topic}
author: Claude prompted by Ha-Duong Minh
date: {YYYY-MM-DD}
paper: {manuscript path}
section: {section identifier}
citation-budget: {N, or "unset"}
---

## Relevance
Why this note exists for this paragraph. Intellectual stakes.

## History of science context
Lineage of the sub-field. Problem origin, paradigm shifts, current
state. Name opposing views with references.

## Cited works — detailed
### {Author Year — short title}
- **Reference.** Author, year, venue, DOI/URL.
- **What the work did.** Method, data, main result.
- **Why this paragraph cites it.** The specific claim it supports.
- **Limitations or critiques.**

## Related but not cited — justified
### {Author Year — short title}
Why not cited (superseded, off-topic, redundant, etc.).

## Methods
Searches run, snowballing seeds, databases, stop condition,
inclusion/exclusion rule, freshness cutoff, preprint policy,
grey-literature policy (if applicable), identifier resolution log,
LLM-assist disclosure.

Citation re-resolution of a finished note: `runbooks/validate.md` (formerly `/related-work-note-validate`).

## Author verification checklist
- [ ] Read each cited primary source (not just abstract)
- [ ] Confirmed claim-to-citation mapping
- [ ] Checked preprints for peer-reviewed updates
- [ ] Agreed with "related but not cited" justifications
- [ ] No in-repo docs cited in place of primary sources

## Bibliography
Alphabetical, biblatex format per Toolchain section above.
```

## Archive the note

After writing, **sequential-blocking** because the receipt needs the final
file: stage the Markdown in project-local `docs/`, then follow
[Zotero Markdown intake](../zotero/references/import.md#markdown-research-notes)
to store it as a Document with a file attachment. Put the paragraph's
manuscript/section and the cited source Zotero library/item keys in the note
metadata and Document provenance; retain any corpus `work_key` values.
Return the requested note path, Document and attachment keys, and live hash
receipt, or the explicit pending reason. `check-staging` does not check notes;
include this note in the run's separate per-note archival inventory. Archive
when produced, never defer it to submission.
