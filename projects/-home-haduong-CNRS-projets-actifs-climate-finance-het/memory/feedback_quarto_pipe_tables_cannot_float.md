---
name: quarto-pipe-tables-cannot-float
description: Captioned pipe tables render as longtables that split across pages; only raw-latex-tabular-in-div floats — tbl-pos on a caption is ignored
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7916be61-b5ab-4c43-9ab3-33af97f51055
  modified: 2026-07-29T13:34:45.444Z
---

In Quarto 1.8 PDF output, a captioned markdown pipe table always becomes a
`longtable`, which cannot float and splits at page bottoms. `tbl-pos` on the
caption attribute (`{#tbl-x tbl-pos="tbp"}`) is silently ignored for pipe
tables.

**Why:** Beta-1 finishing pass (2026-07-29): the author asked for Tables
1/4/5 whole on one page. Two failed attempts (caption attribute, div wrap
around a pipe table) before the working pattern.

**How to apply:** The only pattern that floats is the one `tab_variables.md`
uses: a `::: {#tbl-x tbl-pos="tbp"}` div containing a raw `{=latex}` block
with `\begin{tabular}...\end{tabular}`, caption as the div's trailing
paragraph. Quarto then wraps it in `\begin{table}[tbp]`. Costs: in-cell
`@citations` die in raw latex (use plain text + `nocite:`), and `%`/`&` need
escaping (an unescaped `%` in a header row comments out the row terminator
and yields "Misplaced \noalign"). For a longtable that merely starts too low,
the KISS fix is moving the include down a paragraph so it opens its page.
Related: [[prefer-latex-over-qmd]] — this pain is why.
