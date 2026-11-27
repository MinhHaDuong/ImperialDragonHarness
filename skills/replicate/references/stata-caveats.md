# Stata transcription caveats

Use this reference when the caller has authorized translation of a Stata
package. Missing access to a Stata licence supplies no translation authorization.
Faithful Stata-to-Python execution can establish canonical CRA under
[assessment.md](assessment.md#faithful-stata-to-python-cra), with model, sample,
standard errors, and all required results verified. Disclose the actual method
and native execution status separately; native execution is not a prerequisite.
Preserve the skill's existing scope, comparison, CRR, and [plan-approval boundaries](probe-approval.md).

## Evidence and version boundary

The official manual entries below are from **Stata Release 19**, copyright
2025, checked on 2026-11-27. Page links refer to the entry's printed pages.
Record the package's Stata release, update, `version` directives, explicit
options, storage types, and relevant session settings when known. Unknown
historical settings and effective version behavior stay unknown; current
manuals and table matches cannot establish them.

Keep four evidence kinds separate in `reproduce/README.md`: manual-documented
behavior for the cited release; documentary inference; case-calibrated
implementation choices; and unresolved historical behavior. Apply
[validation.md](validation.md) before using published values to choose a
convention. Preserve the alternatives, calibration targets, and unused-target
freeze there. Keep paper-specific results in the paper project.

## Manual-documented behavior: storage and expressions

- **`generate` defaults are configurable.** Numeric results use `float` unless
  an explicit type or `set type double` changes storage. Record the effective
  setting instead of assuming all generated variables use one precision.
  [Release 19, generate, pp. 1–2 and 5](https://www.stata.com/manuals/dgenerate.pdf#page=1).
- **`replace` can promote types.** The manual documents integer-to-floating,
  longer-integer, and longer-string promotion; `nopromote` suppresses it.
  This supports neither a blanket “keeps its type” rule nor an automatic
  float-to-double claim. [Release 19, generate, p. 2](https://www.stata.com/manuals/dgenerate.pdf#page=2).
- **`egen` needs function-specific inspection.** Its syntax accepts a storage
  type and its functions have their own behavior. The `std()` example contrasts
  default float storage with explicit `double`; it is evidence for that
  example, not every built-in or user-written function.
  [Release 19, egen, pp. 1–2 and 15](https://www.stata.com/manuals/degen.pdf#page=15).
- **Invalid arithmetic yields missing.** Division by zero yields a Stata
  missing value. Preserve that behavior in a translation rather than allowing
  an infinity to enter downstream samples.
  [Release 19, User's guide §13.2.1, p. 2](https://www.stata.com/manuals/u13.pdf#page=2).
- **Subscripts follow observation order.** Without `by`, `x[k]` addresses the
  current dataset's observation k; with `by`, subscripts are group-relative.
  Out-of-range subscripts return missing. Inspect sort order and grouping at
  the statement, rather than substituting panel-relative indexing.
  [Release 19, User's guide §13.7–13.7.2, pp. 12–14](https://www.stata.com/manuals/u13.pdf#page=12).

## GMM: documented facts and documentary inference

**Manual-documented:** `{xb: varlist}` forms a linear combination of the listed
variables; it supplies no implicit intercept. An intercept can be specified
with `_cons` in the list or a separate parameter. `instruments()` includes a
constant unless `noconstant` is specified. Distinguish model regressors from
instruments. [Release 19, gmm, pp. 5 and 13–15](https://www.stata.com/manuals/rgmm.pdf#page=13).

**Manual-documented:** the default estimator is two-step GMM, with
`winitial(unadjusted)` for the initial matrix and `wmatrix(robust)` for the
subsequent matrix. `wmatrix(cluster ...)` is a separate weight-matrix option.
The default VCE follows an explicitly specified weight-matrix type when
`vce()` is omitted. [Release 19, gmm, pp. 2 and 5–7](https://www.stata.com/manuals/rgmm.pdf#page=5).

**Documentary inference:** these separate defaults and the stated direction
from `wmatrix()` to an omitted `vce()` do not establish a reverse override:
`vce(cluster ...)` alone is not documentary proof of clustered second-step
weighting. Treat robust weighting with clustered VCE as an interpretation of
these Release 19 options, not verified execution of an unknown historical
installation. Preserve explicit options and name the remaining uncertainty.

## GEE: limited documented corrections and open behavior

**Manual-documented:** `xtgee`'s `rgf` multiplies the robust variance by
`(N-1)/(N-P)`, where N is the observation count and P the coefficient count.
It is available only with `family(gaussian)` and robust VCE, whether specified
or implied by probability weights. [Release 19, xtgee, p. 4](https://www.stata.com/manuals/xtxtgee.pdf#page=4).

**Evidence limit:** the manual gives exchangeable and autoregressive/stationary
correlation structures separately. Its exchangeable pooled expression does
not establish a universal pooled-pair AR normalization rule.
[Release 19, xtgee, pp. 17–18](https://www.stata.com/manuals/xtxtgee.pdf#page=17).
A convention chosen by matching a paper's tables remains case calibration;
record it under [validation.md](validation.md), not as a generic default.

**Historical/open:** StataCorp's [divisor FAQ](https://www.stata.com/support/faqs/statistics/xtgee-divisor-stata-11/)
explicitly concerns Stata 11 and says it does not apply to recent versions.
It cannot establish a universal current correction. An additional `G/(G-1)`
cluster factor, its combination with `rgf`, and the authors' actual historical
AR normalization remain unresolved by the evidence cited here. Record the
release-specific source or execution evidence needed to settle each case;
matching published values alone cannot do so.
