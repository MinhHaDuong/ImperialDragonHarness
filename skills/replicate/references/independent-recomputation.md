# Independent recomputation of published statistics

This prospective evidence route implements A6 in
[ticket 1580](../../../tickets/1580-replicate-author-review-of-the-two-pilot.erg),
with the original-source qualification in
[the recovered crosswalk](../../../tickets/reviews/t1580/recovered-source.md#additional-original-source-constraints).
When author code for a published statistic is missing, an independently written
producer can still recompute a trivial quantity from existing analysis inputs.
Record that work separately from author-code reproduction. This reference
changes no assessment schema, canonical comparison status, category, or score.

## Decide eligibility before computing

Work sequentially: resolve the target and triviality, record the prospective
method and scope, execute within authority, then compare and report. Each step
needs the evidence retained by the preceding step.

A quantity is trivial here only when existing analysis inputs and authoritative
source definitions uniquely determine its computation before inspecting the
recomputed output. Record the exact variable, units, sample and exclusions,
missing-value handling, weights, denominator, aggregation, and estimator where
applicable, with source anchors. An explicitly defined count or mean can qualify;
a short script or a familiar statistic alone cannot. An unresolved sample,
weight, denominator, or estimator choice remains a named gap. Do not select a
convention by matching the printed value or resolve ambiguity with an assumed
default. Apply `validation.md` to exposure and prospective decisions.

Only execute within the caller's authorized `rerun` perimeter. This route adds
no pre-data arithmetic audit, new data acquisition, model/specification choice,
challenge approval, translation permission, or automatic historical reassessment.
If producing the quantity needs a discretionary scientific choice, retain the
unresolved reason and propose the needed decision under the existing contract.
Missing authority leaves execution not run, even if the arithmetic looks easy.

## Retain production and comparison separately

Use a separate evidence ledger, such as `out/independent-recomputation.csv`,
with one record per stable target, declared scope, and run. Bind it to the
required-output coverage map in `reproduce/README.md`. Retain all planned
records, including failed and unexecuted attempts; a success-only file cannot
represent their coverage. The following fields may point to immutable README
or run-log records for longer provenance, but the linkage must be unambiguous.

| Evidence | Required record |
|---|---|
| Identity | Stable `target_id`, mapping to required canonical `outcome_key` where applicable, `scope_id` and revision, execution perimeter, `run_id`, and timestamp |
| Printed comparator | Authoritative paper/version, page/table/cell or passage, statistic and units, literal printed value, and last-printed-digit precision; preserve conflicting sources as unresolved |
| Prospective method | Triviality rationale and sourced definitions, exact computation and sample/weight/denominator/estimator decisions, recorded before execution |
| Producer | Independently written script path, source revision/hash and lines/function, command, and explicit distinction from missing author code |
| Inputs and environment | Exact retained input paths, representations and hashes, locked interpreter/packages/environment identifiers, and execution log/artifact pointers |
| Production | `production_status`: `recomputed`, `failed`, or `not_run`; full computed value and storage/computation precision only when produced; reason and attempted step for failure, or reason and needed next step for nonexecution |
| Printed comparison | `comparison_result`: `match`, `discrepancy`, or `unresolved`, using the unchanged half-unit-of-the-last-printed-digit rule; comparator rule/precision, signed difference when both values exist, and reason for unresolved evidence |

`recomputed` means that the declared independent producer produced the quantity;
it says nothing about agreement. A successfully produced quantity can have a
strict `discrepancy`. Failed or not-run production leaves its comparison
unresolved, with any unavailable value/difference empty. Missing or nonfinite
values cannot establish agreement; retain their production diagnosis and the
unresolved comparison reason. A missing or ambiguous printed comparator also
leaves comparison unresolved. Retain any produced quantity lacking an exact
comparator under `assessment.md` § Auxiliary estimates, or evaluate a sourced
range/inequality under § Published assertions, with links between records.
Those ledgers cannot substitute for this route's printed-comparison evidence.

Apply `discrepancies.md` to the separate strict miss, cause, and diagnostics;
production success never relaxes the printed-digit rule. Preserve first attempts
and subsequent runs under distinct run IDs, including adverse outcomes.

## Keep assessment and counts distinct

Missing author code stays recorded in the analysis-code-provided assessment,
canonical comparison rows/statuses, and coverage records, with the actual reason.
Do not replace a canonical `not_run` or `missing_input` with `recomputed` or an
independent sidecar match. The canonical CSV vocabulary remains `match`,
`discrepancy`, `missing_input`, and `not_run`; sidecar labels belong only to
this ledger. An independent result supplies no author-code match, canonical
or selected-target CRA/CRR success, six-row category or ACRe promotion. It also
supplies no observed canonical failure merely because its strict comparison
misses. The faithful Stata-to-Python CRA route in `assessment.md` remains
eligible under its own complete evidence requirements; an ad hoc independent
statistic is no substitute for those requirements.

In README, cumulative reports, note drafts, and user output, report separately:

- Author-code-route numeric comparisons and their canonical outcomes, identifying
  any eligible faithful translation as its actual method.
- Independent production totals (`recomputed`, `failed`, and `not_run`) and,
  separately, their strict printed-comparison totals, including unresolved reasons.
- Published assertion outcomes and auxiliary estimates under their own contracts.

State each denominator, scope, and counting unit. Count unique targets within a
scope for coverage; count run records separately for attempts, preserving reruns
without counting them as additional targets. Reconcile stable identifiers across
ledgers and show overlaps explicitly: a produced quantity also retained as an
auxiliary estimate or used in an assertion is one quantity with linked evidence,
not another numeric comparison. Required canonical targets, including unknown
or unexamined coverage, stay in the inventory with their existing disposition.
An independent match cannot remove them or complete an all-match subset. Never
combine author-code matches, independent recomputations, assertions, or auxiliary
estimates into a common “reproduced” numerator or scoring denominator.
