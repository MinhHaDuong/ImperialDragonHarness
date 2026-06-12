---
name: evaluate-all overwrites metrics
description: runner.py evaluate-all overwrites all_metrics.json — run sweeps separately then merge
type: feedback
---

`evaluate-all` overwrites `all_metrics.json` rather than appending. Running it on sweep2_rag after sweep1_census deletes all census data.

**Why:** Discovered during sweep 2 evaluation — had to re-run census and manually merge JSON.

**How to apply:** When evaluating multiple sweeps, either run to separate output dirs (`--output ../results/summary/census` vs `../results/summary/rag`) then merge, or wait for #92 fix.
