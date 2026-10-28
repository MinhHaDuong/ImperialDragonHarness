---
metadata:
  category: writing
  order: 3
name: pdf-finish
description: "Finishing pass on a PDF deliverable — journal submission, preprint deposit, personal page, report handoff. Keyword: finition."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pdf-or-manuscript-path>"
---

# PDF finishing

**When.** The author asks for it, or a deliverable enters finalization —
submission, deposit, upload imminent — and you propose it. **Never during
drafts**: while content moves, pagination polish is churn. This pass
presupposes frozen content.

For language-specific spacing and punctuation, follow `runbooks/typography-finish.md` on the
rendered deliverable during this same finalization pass. Its markup-specific
rules avoid hand-inserting spaces that LaTeX already produces.

## 1. Automate first, paginate by hand never

Layout intent belongs in the header or config, declared once — not in
hand-inserted `\newpage` rounds that any upstream edit re-opens.
For a Quarto/LaTeX build, the standard knobs:

- **Sections on fresh pages** (long-form ≥ 20 pp):
  `\usepackage{titlesec}` + `\newcommand{\sectionbreak}{\clearpage}`.
- **Widows and orphans**: `\widowpenalty=10000 \clubpenalty=10000`.
- **Pipe-table column widths**: pandoc maps the delimiter-row dash counts to
  relative widths — set the ratios there; narrow the label columns, give the
  analytic columns the room. Only if a longtable still splits, one `\newpage`
  before it.
- **Bibliography density**:
  `\AtBeginEnvironment{CSLReferences}{\small\setlength{\parskip}{0.3em}}`.

## 2. Mechanical checks and visual inspection

Record each command actually run, its result, and anything unavailable. Use
`pdftotext` to extract text, `pdfinfo` for page size/count and metadata, and
`pdffonts` for embedded fonts when those tools are available. Check:

- Build logs for unresolved citations/references, following
  `rules/manuscript-build.md`. A compiler exit code and an existing PDF do not
  establish a valid product. A missing log leaves the check unverified.
- Extracted text for replacement characters (`�`) and expected identifiers.
  Font listings and clean extraction are useful signals; they cannot prove
  every glyph rendered correctly.
- Page size (A4 unless the venue specifies otherwise), page count, title and
  author metadata against the intended variant.
- Anonymous variants against a specific list of author names, affiliations,
  acknowledgments, identifying repository URLs and this manuscript's version
  identifiers. Check visible text, metadata and link targets where inspectable.
  Preserve ordinary bibliography DOI/URL references; remove or mask only those
  that identify the author or this manuscript's deposited version.
- DOIs and URLs introduced during finishing: spot-check their destinations and
  record any that could not be checked.

Inspect rendered pages visually for split tables/figures, detached captions,
headings stranded at page bottoms, widows/orphans, clipping and missing glyphs.
Text extraction alone does not establish these layout properties. Inspect all
pages when feasible; otherwise state exactly which pages were inspected and
which remain unverified. Do not claim a complete layout pass from a sample.
No general layout analyzer is required.

The handoff records mechanical results, pages visually inspected, findings and
remaining limits separately. An unavailable tool or uninspected page is a
reported limit, never a passed check.

## 3. Variants in isolated copies

Pin the source revision, then create a fresh worktree or isolated source copy
for each named, anonymous or deposit variant. Include the complete pinned
build inputs, including any ignored bibliography or generated figures. Apply
variant transforms and render only in that copy; leave the author's active
source untouched even if rendering fails. Never use apply/render/restore on
the working source.

Archive the transform script, source revision and supplementary input hashes
beside the release artifacts so the variant can be reproduced. Check the
rendered variant's text, metadata and identifying links before delivery.
