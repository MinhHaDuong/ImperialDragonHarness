---
name: feedback-matplotlib-annotation-autoscale
description: "ax.plot for annotations (leader lines) outside the data area silently autoscales the axes limits, desyncing multi-panel layouts — pin limits after all artists"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 90650ce6-f8eb-473a-9f2a-aef68ef22d35
---

In multi-panel figures, drawing annotation artists with `ax.plot(...)` outside
the data range (e.g. leader lines above a heatmap at negative y) silently
expands that axes' limits via autoscale — even after `imshow`. Sibling panels
keep their tight limits, so rows/columns compress only in the annotated panel
(0446: blue matrix 8.36 px/row vs FP panel 9.05 px/row; author spotted the
misalignment by eye, diagnosis took pixel measurement of separator lines).
`ax.text` does NOT autoscale; `ax.plot`/`ax.add_line` do.

**Why:** a published two-panel figure shipped visibly misaligned through two
review rounds; structural tests and casual PDF inspection missed it.

**How to apply:** after drawing ALL artists on a shared-rows multi-panel
figure, explicitly pin `ax.set_ylim`/`set_xlim` on every panel to the data
extent (annotations stay visible with `clip_on=False`). To verify alignment,
don't eyeball: rasterize and compare separator-line pixel rows across panels
(pattern in [[feedback-figure-verify-worst-case-panel]] spirit — measure, not
look).
