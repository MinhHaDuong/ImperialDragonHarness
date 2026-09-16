---
name: arms-runs-csv-no-nmatched
description: tab_exp2_arms_runs.csv has no n_matched column — use the _view variant for coverage scores
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ef055b24-26d2-4507-8b07-e49345ab2c2d
---

`tab_exp2_arms_runs.csv` does NOT have an `n_matched` column. The cross-evaluation coverage scores live in `tab_exp2_arms_runs_view.csv`.

**Why:** When computing Exp2 coverage statistics, querying the base CSV returns zero rows for n_matched silently.

**How to apply:** Always use `tab_exp2_arms_runs_view.csv` when you need `n_matched`; use the base CSV only for cost, wall_s, turns, inventory_rows.
