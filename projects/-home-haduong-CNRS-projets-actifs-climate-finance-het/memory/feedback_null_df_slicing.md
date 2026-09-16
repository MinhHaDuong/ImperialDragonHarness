---
name: Pass full DataFrame, not a slice, to functions needing all columns
description: Passing a sliced DataFrame to a function that needs unlisted columns silently produces NaN output — grep for the bug pattern before closing stat scripts
type: feedback
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
---
When slicing `null_df` for a join, keep the slice local to the join only. Any helper function that computes statistics (e.g., z-scores using `null_mean`/`null_std`) must receive the full DataFrame — not a projection.

**Why:** In ticket 0084, `_aggregate_subsample_ribbon` was passed `null_cols` (a 4-column slice: year, window, z_score, p_value) instead of `null_df` (which has `null_mean`, `null_std`). The function silently skipped all rows (`has_null_stats = False`) and produced an all-NaN ribbon — no error, no warning, just wrong output that would have reached the plot.

**How to apply:** When writing a function that takes a DataFrame and accesses columns by name, either (a) pass the full frame and let the function select, or (b) document the required columns in the function signature. Before closing any stat-pipeline PR, grep for `null_cols\s*=.*\[` or similar projection-then-pass patterns and verify the sliced frame has every column the callee needs.
