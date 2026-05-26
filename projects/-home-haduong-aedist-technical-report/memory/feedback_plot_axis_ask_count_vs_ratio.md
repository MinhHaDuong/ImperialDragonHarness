---
name: plot-axis-ask-count-vs-ratio
description: Ask whether the Y-axis should be an absolute count or a ratio before writing a plot script
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cff971c9-2443-4bea-b53a-cabf6bfa7c03
---

When a ticket specifies a Y-axis metric derived from two CSV columns (e.g. "primary source rate"), ask the user whether they want the absolute count or the ratio before writing the script.

**Why:** Ticket 0265 specified `src1_primary / src1_present` as the Y-axis. The user corrected this mid-review — they wanted `src2_present` (absolute count). The ratio also had an undefined-denominator problem when `src1_present=0`. One clarifying question upfront would have saved a full iteration.

**How to apply:** Before implementing any plot with a computed Y metric, confirm: "Do you want the absolute count or the ratio?" Ratios introduce denominator edge cases; absolute counts with a diagonal reference line (Y=X) are often more interpretable and avoid the problem entirely.
