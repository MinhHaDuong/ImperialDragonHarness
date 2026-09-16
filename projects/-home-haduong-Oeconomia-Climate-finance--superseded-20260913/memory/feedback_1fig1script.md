---
name: feedback_1fig1script
description: Every figure must have its own plot_fig_*.py script — no shared plotting modules
type: feedback
---

1 figure = 1 script. No exceptions. No `*_plots.py` modules collecting multiple figures.

**Why:** The project convention is that every figure script follows `plot_fig_*.py` naming, one script per output figure. This keeps figures independently runnable, testable, and traceable in the Makefile.

**How to apply:** When splitting god modules that contain plotting code, extract each figure into its own `plot_fig_*.py` script. Never create a shared `*_plots.py` module as a dumping ground for multiple figures.
