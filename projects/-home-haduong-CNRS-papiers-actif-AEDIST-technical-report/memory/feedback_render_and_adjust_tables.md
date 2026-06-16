---
name: feedback_render_and_adjust_tables
description: "After ANY table modification, always render the PDF and check/adjust every table's column widths"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

**Standing author instruction (2026-06-15):** for any LaTeX document with tables (manuscript `main.tex`, the report, the slides), after ANY change that touches a table — new column, changed content, new caption, edited colspec, or even a global edit that could reflow — **always render the PDF and check/adjust the column widths of ALL tables** before treating the change as done. Do not assume a table that fit before still fits.

**Why:** a table that was fine can overflow (overfull `\hbox`, text spilling into the margin or colliding) the moment a column is added or content lengthens. Reading-3 added a 5th column to `tbl:status-difficulty` ("Avg. detection prob. (Exp 2, 1D)") and converted the Annex B agents table to `tabularx` — column fit must be verified by rendering, never assumed.

**How to apply:**
- Build with logs: `cd slides/manuscript && tectonic -r 2 --keep-logs main.tex`, then `grep -n 'Overfull \\hbox' main.log` and map each to its table.
- Fix the colspec until clean: prefer `tabularx{\linewidth}{… >{\raggedright\arraybackslash}X}` for the wide text column; otherwise tune `p{…}` widths, abbreviate headers, or drop to `\small`/`\footnotesize`. Keep numeric columns `r`, short labels `l`.
- This is a manual QA step (judgment on which column to shrink), so it lives as a working rule here — not a hook. Consider mirroring it into `.claude/rules/writing.md` as a project convention checked at `/review-pr-prose`.
- Applies to every table in the document, not only the one just edited.
