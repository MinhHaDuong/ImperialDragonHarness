---
name: feedback_argparse_defaults_drift
description: "When Makefile output paths change, argparse defaults in plot scripts go stale and need updating too"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ce9fb20-3b79-41a4-90ba-e2b94004e133
---

When an output path moves (e.g., figure relocation from slides/ to report/), update both:
1. The Makefile target path
2. The `argparse` `default=Path(...)` in the generating Python script
3. Usage examples in module docstrings

**Why:** PR #536 relocated 4 figures from `slides/inputs/generated/` to `report/inputs/generated/`, updated Makefiles and tex/md references, but missed the argparse defaults in `plot_capability_dag.py`, `plot_capability_timeline.py`, `plot_cost_quality.py`. Ticket 0301 tracks the fix.

**How to apply:** After any Makefile output path change, grep `src/` for the old path string before declaring done.
