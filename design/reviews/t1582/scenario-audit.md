# Published assertion scenario audit

Ticket 1582; 2026-11-27. Documentation audit with synthetic examples, not
scientific estimates or a historical-case reassessment. Authority: parent
1575 B6 exact author relay and child 1582; merged B3 eligibility is retained.

| Scenario | Expected evidence and decision | Contract anchor |
|---|---|---|
| Positive control: sourced scalar x in explicitly closed [0.05, 0.12], produced x = 0.08 | confirmed assertion; no exact published value or match fabricated | assessment.md § Published assertions: scalar membership, separate ledger |
| Boundary: sourced x > 0.24, produced x = 0.24 | not_confirmed; changing to >= would incorrectly confirm | Same section: preserve inequality operator |
| Boundary: sourced x >= 0.24, produced x = 0.24 | confirmed assertion, still no exact statistic match | Same operator rule |
| Ambiguous bare printed 0.05–0.12, with no clarified target or inclusivity | unresolved; do not infer a closed interval | Same section: unknown meaning/inclusivity |
| Universal collection claim, required values 0.08 and 0.13, closed [0.05, 0.12] | not_confirmed with 0.13 counterexample; inspecting only 0.08 cannot confirm | Same section: quantifier and complete coverage |
| Universal collection claim, only one in-range member inspected | unresolved, required coverage retained | Same section: complete sourced assertion |
| Source reports extrema 0.05 and 0.12; reproduced extrema 0.06 and 0.11 | membership alone cannot certify reported endpoints; preserve both endpoint comparisons under unchanged numeric tolerance | Same section: reported endpoint statistics |
| Source says a confidence interval is contained in [0.05, 0.12]; reproduced interval [0.04, 0.10] | not_confirmed despite midpoint inside; whole interval violates containment | Same section: interval objects and sourced relation |
| Assertion confirmed while a separate required numeric statistic is unexamined | exact comparison remains unresolved; no CRA or six-row success inferred | Separate counts/category rule; SKILL reproduce/report; rules.md §§ 1–2 |
| x > 0.24, produced x = 0.2399 | not_confirmed; printed-digit tolerance cannot expand predicate | Bound preservation rule |
| Produced estimate has no exact comparator but supports a sourced assertion | auxiliary full value linked by assertion evidence; neither row enters numeric match totals | Auxiliary/assertion separation and output guidance |

Audit outcome: positive control confirms only the assertion; strict-bound,
collection, and interval counterexamples expose the forbidden substitutions.
All required numeric targets remain in scope; canonical categories, numeric
status vocabulary, article tolerance, legacy cases, and human signing retain
their existing rules. No wording-pin tests are introduced.

Parallel contract inspection covers SKILL reproduce, selected-claim freeze,
report/output guidance, assessment schema/selected target/comparison/auxiliary
sections, and report rules. No unrelated change to validation, Stata caveats,
or worked-example mapping is needed for this assertion-only contract.
