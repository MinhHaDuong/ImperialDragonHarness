---
name: feedback-figure-verify-worst-case-panel
description: "When visually verifying a multi-panel figure for title/label overlap, inspect the worst-case panel (longest/two-line labels), never a representative easy one"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: eddfaf5e-039e-4186-8b55-bc86650e69c0
---

When a figure has several panels and the exit criterion is visual ("titles do
not overlap axis labels"), inspect the panel **most likely to fail** — the one
with the tallest/longest/multi-line title or labels — not a convenient
representative.

**What it caused (2026-06-03, PR #665 / ticket 0357):** redesigning
`fig_spider_cross_exp` from a 3×3 quincunx to a compact GridSpec, I rendered the
PDF and inspected only the **E1** panel, whose title is a single line
(`E1 (param.)`). It cleared. I declared the overlap criterion met. The
verify-gate's `/review-pr` re-rendered and found titles still overlapped the
polar dimension-label ring in **4 of 5 panels** — exactly the ones with
**two-line** titles (`1N\n(naïf, 1 tour)`, `5N\n(optim., 5 tours)`, etc.), which
sit lower and collide. REROLL. Fix: `set_title(y=1.55)` (pad is unreliable on
polar axes) + wider `hspace`.

**Why:** structural/count tests (5 polar axes, no `add_subplot(3,3)`) give zero
signal on visual overlap — only a render check does, and a render check of the
easy panel is worse than none because it manufactures false confidence.

**How to apply:**
- List the panels' titles/labels; pick the longest or any multi-line one and
  crop-inspect *that* at high dpi (200+). If several differ, check 2-3 extremes.
- Two-line titles on polar axes overlap the label ring far more than one-line;
  treat them as the controlling case.
- Pair with [[feedback_verify_artifacts_after_fix]] (rebuild before commit) and
  [[feedback_compute_before_figure]].
