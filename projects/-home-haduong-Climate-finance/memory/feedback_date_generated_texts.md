---
name: date-generated-texts
description: Generated/rendered documents must carry the correct current date — never a stale pinned date
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 352d5761-eab8-421e-8926-7931ba20d97f
  modified: 2026-07-24T12:35:33.487Z
---

When generating or regenerating a document (PDF render, letter, report),
its date must be right.

**Why:** author rule 2026-07-24 — both cut-pass comparison PDFs rendered
"March 26" because data-paper.qmd pinned the original submission date;
a stale date on a revised manuscript misrepresents the revision.

**How to apply:** prefer render-time dates (`date: today` in Quarto,
`\today` in LaTeX) for working documents; pin an explicit date only for a
frozen submission artifact, and update it deliberately at each submission
event. Data-provenance dates ("as of YYYY-MM-DD") come from the harvest
run, not hand-written prose — wire them through vars when touched.
