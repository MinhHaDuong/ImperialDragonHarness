---
name: Analytical null as visual overlay
description: Analytical null ribbon overlaid on MC ribbon in zoo figures, not a standalone validation script
type: feedback
originSessionId: b0ad69a4-551a-4c51-ad1d-3c2e0e738f34
---
Render analytical null as a second semi-transparent `fill_between` overlaid on the MC ribbon in the zoo figures. Both with alpha ≈ 0.25; coincidence is visible as a merged patch.

**Why:** User's preference — "plot in overlay when available. Not as a colored hashed area, both MC and theory with alpha so coincidence can be seen." A standalone `validate_null_model.py` script would work but wouldn't be immediately legible. The overlay makes agreement vs. divergence instantly visible without opening a report.

**How to apply:** When implementing ticket 0115, `plot_zoo_results.py` gets a second optional `--analytical-null <csv>` argument. MC ribbon and analytical ribbon draw side-by-side as overlapping fills. Analytical CSVs live in `tab_analytical_null_*.csv` (separate from MC `tab_null_*.csv`). Only available for S1/S2/L1/C2ST; G methods show MC ribbon only.
