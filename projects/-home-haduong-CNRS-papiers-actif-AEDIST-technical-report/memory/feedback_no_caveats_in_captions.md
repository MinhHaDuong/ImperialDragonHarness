---
name: feedback_no_caveats_in_captions
description: "Figure/table captions state plainly what the figure shows — no caveats, hedging, or method qualifications (those go in body/annex)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

**Standing author instruction (2026-06-15): no caveat and hedging in captions.**

A figure or table caption states plainly *what the figure/table shows and how to read it* — the axes, the bars, the message. It does NOT carry caveats, hedges, limitations, or methodological qualifications. Those belong in the body or the annex.

**Examples of what to MOVE OUT of a caption:** "OSM matching relies on name-only fuzzy search, so its sparser coverage reflects both genuine mapping gaps and the weaker matcher" (a method caveat — removed from the `fig:longtail` caption); "an existence proof rather than a validated detector" style hedges; "we did not measure …" disclaimers; "details/provenance are in Annex …" pointers when they are just hedge-padding.

**How to apply:**
- When writing or reviewing a caption, strip any caveat/hedge/limitation sentence and relocate it to the relevant body paragraph or annex.
- Pairs with the standalone-caption policy (text + captions standalone at the maths/ideas level, code only in annexes — ticket 0633) and the render-and-adjust rule ([[feedback_render_and_adjust_tables]]).
- A caption can still carry a plain `\ref` to the annex for *detail*, but not a sentence whose job is to hedge or qualify the result.
