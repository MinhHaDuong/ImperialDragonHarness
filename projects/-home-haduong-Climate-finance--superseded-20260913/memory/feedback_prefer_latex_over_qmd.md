---
name: prefer-latex-over-qmd
description: "Author decision 2026-07-29 — next paper deliverable starts in plain LaTeX, not Quarto/QMD"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7916be61-b5ab-4c43-9ab3-33af97f51055
  modified: 2026-07-29T11:45:39.411Z
---

"QMD is so painful. Next time we will use LaTeX from the get go" — author,
2026-07-29, at the end of the RDJ-26561 beta-1 finishing pass.

**Why:** The finishing pass fought Quarto more than LaTeX: pandoc renders
pipe tables as longtables (which cannot float — needed `tbl-pos` attributes
and a generator rewrite to tabular), `titlesec` clashes with Quarto's
document class (had to fall back to `needspace`), and layout intent goes
through `include-in-header` indirection. The `{{< meta >}}` vars machinery
is the one part worth keeping.

**How to apply:** When starting a NEW paper deliverable, propose plain
LaTeX (with the vars pipeline emitting `\newcommand` macros instead of
YAML) rather than a `.qmd`. Existing QMD deliverables stay as they are —
this is a from-the-get-go preference, not a migration mandate.
