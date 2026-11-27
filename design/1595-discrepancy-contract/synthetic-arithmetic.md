# Synthetic arithmetic scenario output

Generated 2026-11-27. Synthetic decimal inputs only; no paper findings or empirical execution.

| Scenario | Computed result |
|---|---|
| printed 1.234; recomputed 1.235; printed half-unit .0005 | difference 0.001; strict match=False |
| illustrative estimate SE 0.1, no scientific margin supplied | d/SE=0.01; descriptive only, equivalence unavailable |
| same finite pair at two digits | 1.2 vs 1.2; equal=True |
| same finite pair at three digits | 1.23 vs 1.24; equal=False |
| rounding 1.25 to two significant digits | 1.3 |
| rounding -1.25 to two significant digits | -1.3 |
| rounding 0 to two significant digits | 0 |
| rounding 999.5 to two significant digits | 1000 |
| rounding 0.00125 to two significant digits | 0.0013 |

The example declares two eligible IDs: one finite pair above and one missing
output. Thus eligible=2, finite-pair denominator=1, unresolved=1 at both
precisions. Two-digit equality=1 and difference=0; three-digit equality=0
and difference=1. Strict article mismatch remains, regardless of rounding.
These counts are derived from this explicitly synthetic set, not a coverage claim.
