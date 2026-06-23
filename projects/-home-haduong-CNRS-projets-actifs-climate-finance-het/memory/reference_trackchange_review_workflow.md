---
name: reference_trackchange_review_workflow
description: Marked-PDF review loop for interactive manuscript revision — \rradd blue track-change macro + per-turn quarto render
metadata: 
  node_type: memory
  type: reference
  originSessionId: 130172cd-69de-440c-879e-e35c7f4a91f5
---

Effective loop for revising Œconomia manuscript prose with the author (used
2026-06-18 on §3.1, PR #815): make edits in `content/manuscript.qmd`, mark each
insertion so it shows in the rendered PDF, render, and let the author reply in
CLI (not by annotating the PDF — author finds that inconvenient; CLI replies +
agent edits the qmd is the agreed channel, see [[feedback_parallel_work]]).

**Track-change mechanism (xelatex/Quarto):**
- Inline insertions: a header macro `\newcommand{\rradd}[1]{\textcolor{blue}{\uline{#1}}}`
  (needs `\usepackage{xcolor}` + `\usepackage[normalem]{ulem}`), wrapped in a
  Pandoc raw span: `` `\rradd{...}`{=latex} ``. Raw-LaTeX content holds no markdown
  (no @cites, no `*emph*`); escape `%` as `\%`, `$` as `\$`.
- Block insertions (lists, multi-paragraph, content with citations): wrap in
  `` `\begingroup\color{blue}`{=latex} `` … `` `\endgroup`{=latex} `` so the inner
  text stays normal markdown.
- Render only the one doc (avoids the whole-project include scan failing on a
  sibling's missing table): `quarto render content/manuscript.qmd --to pdf`.
  A fresh worktree lacks gitignored build artifacts — copy `content/{figures,tables,_includes}`
  from the main checkout first or the render errors.
- **Accept** = strip the markup to clean source (unwrap `\rradd`, drop the color
  blocks, remove the header macro). The tracked-changes record is not lost: it is
  the git diff against the pre-branch commit, regenerable via latexdiff anytime.

Keep prose in HET academic register throughout — see [[feedback_het_register]].
