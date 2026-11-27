# Eight rules for an I4R replication report

Source: Abel Brodeur, "Pre-Games Meeting", Institute for Replication,
November 2026, slides 3-16, as converted in replicator's
`doc/brodeur-i4r-pregames-2026/2026_i4r-pregames.md`. The rules below
restate the talk. The I4R report template chosen from `templates/INDEX.md` is the
authoritative format.

Written for a team that is not all economists. Two words first:

- **Reproduction** (computational reproducibility) asks whether the
  authors' data and code give the numbers printed in the paper. Nothing about
  the method is questioned yet.
- **Robustness** asks whether the result survives reasonable changes:
  another way to compute standard errors, without outliers, another
  definition of a variable. A result that survives is *robust*; one that
  breaks under a reasonable change is *fragile*. Both findings are useful.

A **specification** is one exact way to estimate the model: variables, sample,
estimator and standard errors. A **coefficient** is the estimated effect; its
**standard error (SE)** measures its uncertainty; the **p-value** says how
surprising the estimate would be if the true effect were zero.

## 1. The Reproducibility Table is always present

Retain all six rows. Mark established categories Fully, Partially, or No;
show unresolved rows as "not yet assessed", with their reason. If the chosen
template fixes the three category columns, leave them unmarked for an
unassessed row and place its status beside it. Inspection establishes
provision; output comparisons establish numerical execution. A verified
from-raw impossibility may have No with an explicit provision-based basis,
distinct from an observed failed run (`assessment.md`).

| | Fully | Partially | No |
|---|---|---|---|
| Raw data provided | | | |
| Cleaning code provided | | | |
| Analysis data provided | | | |
| Analysis code provided | | | |
| Reproducible from raw data | | | |
| Reproducible from analysis data | | | |

*Raw data* is what the authors collected or downloaded. *Cleaning code*
turns it into *analysis data*, the file the regressions read. You can fill the
first four rows before the Games when their evidence permits; unknown
coverage remains visible. The six-row table always includes Fully and
unassessed rows. In the separate detailed statistic comparisons, show only
the results that did not reproduce; individual matching statistics are not
listed there. Estimates retained without authoritative printed numeric
comparators are separate auxiliary evidence under `assessment.md` § Auxiliary
estimates, outside discrepancy counts and scoring denominators. Published
range/inequality assertions have separate confirmed, not-confirmed, or
unresolved evidence under `assessment.md` § Published assertions. Preserve
their actual targets and boundaries; keep them visible separately from the
detailed statistic list, numeric counts, and canonical categories.

For an explicitly requested selected target, additionally show its separately
labelled six-row table and scope ID under `assessment.md` § Selected-target
assessment. The canonical whole-paper table keeps its meaning; selected
categories never substitute for its unknown rows or its grid criteria.

## 2. Three-digit precision, always beside the original

Report every statistic to three digits: coefficient, SE, and p-value or
confidence interval. Put each robustness result next to the original
estimate. If the paper prints no number (only a figure), use the reproduced
value as the original. A check with no original to compare with is
probably unfair or unusable: ask I4R.

This is a report-display rule; stored comparison and auxiliary CSV values stay
at full precision. Preserve published range/inequality operators and boundary
semantics in the separate assertion evidence; display rounding never changes
the predicate or supplies an exact published comparator. A reproduced robustness
baseline supplies no invented printed comparator for reproduction scoring. Preserve produced estimates
without such a comparator under the separate auxiliary contract in
`assessment.md`; it grants no new check-selection or execution authority.

## 3. Table layout

The first column is the reproduced original. Then add one column (or one
pair) per alteration. The table notes name the original table number and
say exactly what changed.

## 4. Be fair

The point is not to break the paper; it is to do good science. Do not hunt
for the specifications that remove significance or flip a sign. A report
that finds everything robust is as valuable as one that finds the results
fragile, as long as the checks are fair. This is why a person, not an
agent, signs the robustness plan.

## 5. Stay in scope

Robustness checks focus on the paper's main models. Heterogeneity
analyses (does the effect differ by group?) and extensions (new questions)
are not robustness. I4R does not feature them. They may go in the report as
extras.

## 6. The report is itself reproducible

Share all new code, and new data where allowed, with the report. Scripts
write their numbers to a table file (CSV), so anyone can rerun them and get
the same table.

## 7. The robustness menu

Checks the paper does not already run belong in the menu. A robustness check
asserted in the paper without numbers or code is eligible for the plan and
cannot be rejected as a duplicate on that ground. Propose it when it bears on
the main result; the signer may reject it for another explicit reason.
Proposal does not authorize execution. Examples:

- undisclosed deviations from a pre-analysis plan;
- fixing coding errors (a fix counts as a robustness check);
- other clustering, weighting of observations, or computation of standard
  errors or indices;
- parametric against non-parametric approaches;
- outliers and other sample restrictions;
- redefining variables (treatment intensity instead of a yes/no indicator);
- re-coding the analysis in other software (from Stata to R, say).

If the paper does not reproduce or its data are badly flawed, robustness may
be impossible. Consult I4R.

## 8. Summarise the method; split the day

The report's summary of the paper names its method, for example "the paper
reports a laboratory experiment" or "a panel regression on country-year
data". On the day, the morning goes to reproduction, data problems and coding
errors; the afternoon goes to robustness and writing. Do the mechanical work
(does the code run?) before the Games, and keep the day for teamwork.
