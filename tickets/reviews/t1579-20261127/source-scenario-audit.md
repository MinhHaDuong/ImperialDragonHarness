# Auxiliary estimate contract and scenario audit

Ticket 1579; documentation only. Sources are the accepted receiving record
(parent 1575 B5, child 1579) and the current local skill/schema/report rules.
No foreign reads or numerical runs are needed. The prior generic out/*.csv
heading/schema and report rounding/count wording lacked an auxiliary boundary.

| Scenario | Before | After |
|---|---|---|
| Authorized package run produces an estimate without printed numeric comparator | No explicit retention schema apart from comparison CSV | Full-precision auxiliary row plus producer/specification/route/scope and run provenance |
| Auxiliary rows included by a broad out/*.csv count | Broad schema and discrepancy output wording | Explicit comparison-file scope; auxiliary excluded from statuses, counts, all score denominators and canonical/selected scoring |
| Successful estimate has no comparator | Could be forced into comparison status | No invented match or missing_input/failure solely for absent comparator |
| One model succeeds without comparator and another fails or lacks an input | No explicit auxiliary/failure separation | Retain produced row; preserve actual failure/block reasons in existing run/coverage records |
| Authoritative printed comparator exists (positive control) | Canonical comparison schema/status/tolerance | Same canonical comparison rows, rules, and scoring |
| Required declared target lacks a verified comparator | Existing unresolved scope/completeness rules | Auxiliary retention does not drop target or erase gap; existing rules still govern |
| Qualitative/footnote inventory or new robustness specification | Author/inventory/signing boundaries held | No inventory ruling or execution authority added |

Preservation checks compare canonical comparison-column table, six-row status
tables, assessment JSON/criteria/selected-target rules, and all manifest intake
text against base. Heading narrowing and explanatory boundaries are necessary
documentation edits, not a canonical schema/status change. Rule 2's display
precision is clarified to leave stored CSVs full precision; comparison tolerance,
robustness selection/signature, translation eligibility, and publication gates
remain unchanged. No wording tests, generic helper, or scientific outputs.
