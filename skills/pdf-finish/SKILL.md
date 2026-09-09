---
name: pdf-finish
description: "Finishing pass on a PDF deliverable before it leaves the workshop — journal submission, preprint deposit, personal page, report handoff. Automates pagination through header knobs, verifies the result with a scripted text sweep rather than by eye, and treats each named variant as a reproducible transform layer. Keyword: finition."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pdf-or-manuscript-path>"
---

# PDF finishing

Was `rules/pdf-finishing.md`, resident in every session until 2026-09-09; its
trigger is a task, not a file, so it is a skill (ticket 0572).

**When.** The author asks for it, or a deliverable enters finalization —
submission, deposit, upload imminent — and you propose it. **Never during
drafts**: while content moves, pagination polish is churn. This pass
presupposes frozen content.

## 1. Automate first, paginate by hand never

Layout intent belongs in the header or config, declared once — not in
hand-inserted `\newpage` rounds that any upstream edit re-opens (cost of
skipping: eight interactive re-render rounds on one page-perso variant,
2026-07-22). For a Quarto/LaTeX build, the standard knobs:

- **Sections on fresh pages** (long-form ≥ 20 pp):
  `\usepackage{titlesec}` + `\newcommand{\sectionbreak}{\clearpage}`.
- **Widows and orphans**: `\widowpenalty=10000 \clubpenalty=10000`.
- **Pipe-table column widths**: pandoc maps the delimiter-row dash counts to
  relative widths — set the ratios there; narrow the label columns, give the
  analytic columns the room. Only if a longtable still splits, one `\newpage`
  before it.
- **Bibliography density**:
  `\AtBeginEnvironment{CSLReferences}{\small\setlength{\parskip}{0.3em}}`.

## 2. The checklist — verified by script, not by eyeballing

Sweep the rendered PDF with a text extractor and check mechanically:

1. No table or figure split across pages; caption on the same page as its float.
2. No heading as the last line of a page; no one- or two-line widow above a
   heading at a page top.
3. No missing glyphs (grep the extraction for `<?>` replacement characters,
   check the embedded font list) — math-mode symbols, not text-mode Unicode,
   for ≈/≤/… in Latin Modern.
4. Page size intentional (A4 unless the venue says otherwise); page count and
   metadata (title, author) match the variant.
5. Identity matches the variant: an anonymous build carries zero
   de-anonymizing strings (grep the author name, repo URLs, DOIs); a named
   build carries the restored links.
6. Links resolve: spot-check DOIs and URLs added at finishing time.

Eyeballing stays mandatory for what a script cannot see (memory
`feedback_visual_verify_citations`) — but the pagination sweep is script work,
and a pass that only looks is not this pass.

## 3. Variants are transform layers

A named or deposit variant (HAL, page perso) is a script that applies string
transforms to the shared source, renders, and reverts — apply, render, restore.
Archive the script beside the release artifacts so the variant is reproducible.
Reference implementation: `releases/hal_variant.py` in the Œconomia climate
finance paper (2026-07-22).
