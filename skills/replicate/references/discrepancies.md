# Discrepancy diagnosis and magnitude

Use this procedure alongside `scientific-appraisal.md` to explain discrepancies
in the cumulative report. Keep the first-run observation, frozen comparisons,
strict article match/miss counts, and half-unit-of-the-last-printed-digit rule.
Neither a diagnostic nor scientific confirmation changes them. This contract
adds no CSV status, category, legacy rescore, or execution authority.

## Establish what differs before naming a cause

For every discrepancy, retain target/scope ID, source version and locations,
values at available precision, code/input/environment identifiers, and which
of these comparisons it represents:

- **Internal article inconsistency:** two article passages, tables, figures,
  or SI entries disagree with one another. Retain both locations. This is
  source evidence, not an executed reproduction difference.
- **Printed/recomputed difference:** an authoritative printed target differs
  from an executed value under its frozen comparator. Link the comparison row
  and run evidence. An internal inconsistency can leave target interpretation
  unresolved; do not silently choose the entry that matches the output.

Record observation, cause, and scientific consequence separately. An internal
inconsistency alone does not establish that either number is a typo. Qualify
causes with discriminating evidence:

| Qualification | Evidence and limit |
|---|---|
| Typo or swapped labels | Cite correction/erratum or trace the value-to-label mapping through independent source/code/output evidence. A suspected correction stays an inference, with alternatives and uncertainty. |
| Rounding | State the source precision and rounding operation; demonstrate that it explains the observed difference. Approximate closeness alone is insufficient, and the frozen comparator still governs the strict outcome. |
| Tested Monte Carlo variation | Identify the actual random mechanism and justified uncertainty of the difference under the protocol below. Compatibility with that mechanism supports a bounded explanation; it does not prove the implementation correct. |
| Substantive or unresolved | Give the evidenced consequence for the claim when established; otherwise retain unknown cause and unresolved impact. Size or a failed diagnostic alone establishes neither substantiveness nor harmlessness. |

Preserve competing explanations until evidence distinguishes them, including
adverse or inconclusive diagnostics. Present these qualifications beside the
strict outcomes, following `report-style.md` for substantive context first.

## Prespecify the diagnostic and its limits

Before inspecting the differences to be evaluated, record the stable eligible
target set, scope, units, signed-difference direction, SE source, scientific
margin and rationale, uncertainty method, dependence assumptions, decision
rule, and rounding/count convention in the existing plan/README evidence.
Use signed difference `d = recomputed - printed` and also show `abs(d)`.
If differences were already inspected, date the choice and label the analysis
retrospective; do not call a selected threshold prespecified. No universal
0.1-SE cutoff is authorized.

Report `d / SE` (and its absolute magnitude) only when a finite, positive,
identified estimate SE refers to the same quantity and units. Name whether it
is printed or reproduced and why it is suitable; an SE-row or p-value-row
does not automatically have an applicable estimate SE. Missing, zero, or
incompatible SEs leave the ratio unavailable, with reason. This ratio is
descriptive and is not the SE of the difference or a test of equivalence.

A formal negligibility claim requires justified bounds in scientifically
meaningful units and valid inference for the difference, including dependence
between estimates from the same data and uncertainty from simulation where
relevant. A TOST or equivalent confidence-interval procedure is appropriate
only with its assumptions and error level specified; failure to detect a
difference does not establish equivalence. Retain an inconclusive outcome
when the evidence cannot exclude differences outside the chosen bounds.
Lakens (2017), pp.355–356, supports prespecified meaningful bounds and the
two-one-sided-test logic ([primary paper](https://pure.tue.nl/ws/portalfiles/portal/80918653/lakeequi2017.pdf)).

Do not substitute the original model's SE for uncertainty of a dependent
recomputed-minus-printed difference. Account for the printed value's rounding
and unavailable precision; it is not automatically an exact random-variable
realization. With inadequate joint uncertainty, covariance, or comparator
precision, mark formal equivalence unavailable and explain the missing evidence.
A small descriptive ratio still leaves cause and scientific impact to appraisal.

## Monte Carlo mechanisms

Morris, White, and Crowther, §4.1, explains deterministic pseudo-random states;
§5.2 and Table6 quantify finite-repetition simulation uncertainty
([author preprint](https://arxiv.org/html/1712.03198v3)). Their formulas depend
on the performance measure and assumptions; they are not universal formulas
for every stochastic estimator.

For identical inputs, code/software and versions, complete RNG states/streams,
draw order, seeds, and deterministic execution, the expected Monte Carlo
difference is zero. A repeated seed alone does not establish those conditions.
Investigate any residual difference through logged states, versions, parallel
execution, input and algorithm evidence; do not automatically attribute it to
Monte Carlo noise. Translation can change the RNG or consumption order even
with the same seed; retain actual port differences and unknowns.

When different streams or simulation realizations are legitimately compared,
use an MC SE of the **difference**, with its method and assumptions, rather
than either run's MC SE alone. The variance identity is
`Var_MC(A-B) = Var_MC(A) + Var_MC(B) - 2 Cov_MC(A,B)`.
Independence must be justified before dropping covariance; matched/common
random draws need their joint uncertainty. Retain repetition counts, statistic,
stream relation, MC SE source/calculation, and the prespecified diagnostic
rule. Report `d / MCSE(d)` only for a finite positive denominator; a zero
MC SE requires direct deterministic comparison, and unknown MC SE/covariance
stays unavailable. Compatibility with simulated uncertainty is distinct from
formal equivalence under a scientific margin. Do not assume independent
repetitions or transfer Table6 formulas to correlated/MCMC output without a
method appropriate to that process.

## Second-significant-digit diagnostic

Preserve the same declared eligible numeric target IDs for the two- and
three-significant-digit descriptive comparison; never select only favorable
misses or change the scope after observing differences. For each finite pair,
round the retained exact decimal inputs to two significant digits: for nonzero
`x`, choose `e` with `10^e <= abs(x) < 10^(e+1)`, set `q = 10^(e-1)`, then
round `x/q` to the nearest integer with exact ties away from zero and multiply
by `q`. Zero rounds to zero and signed zeros compare equal. Retain storage
and conversion methods as in `assessment.md` § Comparing two reproductions.
Use the same operation with `q = 10^(e-2)` for three digits. Compare numbers,
not formatted strings; a carry may change their exponent.

Report eligible total, finite paired denominator, counts of equality and
difference after each rounding, plus unresolved IDs/count/reasons. Each eligible
target appears once in either the finite-pair denominator or unresolved set;
use the same denominator at both precisions. Missing/nonfinite values are
unresolved, never matches or exclusions hidden from the count. Also retain
per-target rounded values and unrounded differences in existing report evidence.
Here “second-digit differences” means inequality after rounding to two
significant digits, not counting a character in a formatted string. These are
descriptive counts, distinct from the unchanged strict article verdict totals
and the separate three-significant-digit cross-reproduction agreement ledger.
No two-digit result widens the article tolerance or certifies port agreement.

## When a check overturns a key result

State which declared claim changes and whether the change concerns sign,
magnitude, uncertainty, or interpretation. Discuss the competing specifications'
estimands, sample, functional form, and inference. For count outcomes, address
zeros, their treatment, and the model's assumptions when relevant; otherwise
state why this issue does not apply. Cite actual article/SI, preregistration,
and verified field-practice sources for the selection criteria and retain
missing or conflicting evidence. Distinguish a documented prior justification
from a retrospective rationale. Ask explicitly whether the supported selection
criteria justify the reported specification over the alternative and what
specification search is documented or remains unknown. A reversal alone
supplies no evidence of the authors' intent or undisclosed search.

## Evidence and execution boundary

Arithmetic on existing authorized, provenance-bearing outputs can calculate
these descriptive diagnostics without producing new empirical estimates.
New model fits, simulations, repetitions, corrected estimates, or sensitivity
checks require coverage by the authorized rerun perimeter or the existing
approved challenge plan under `probe-approval.md`; do not infer authority from
calling a check a diagnostic. Retain unavailable evidence instead of running
an unsigned extension. This procedure does not add the separate pending1593
pre-data published-arithmetic audit or change frozen reports.
