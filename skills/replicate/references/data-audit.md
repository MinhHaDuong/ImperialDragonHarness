# Data audit during reproduction

Audit joins and variable constructions within the applicable reproduction
scope. Work sequentially: locate the authors' input stage, record diagnostics
on those inputs, and then trace consequences into constructed variables and
samples. Keep evidence in `reproduce/`, with source paths and line, page,
output, or log anchors. Carry any declared selected scope ID; retain the
whole-paper coverage gaps without expanding a selected execution request.

## Join audit

For each relevant merge or join, record:

- The producing code location, input files and versions, join stage, join
  type, and key expressions as coded. Inspect the inputs at the authors'
  actual join stage, preserving their preceding transformations. Measure
  before any checker-added normalization or correction; a cleaned-key check
  cannot replace this baseline.
- Input row counts and distinct-key counts on each side, missing keys,
  duplicate keys and their multiplicities, expected and observed key
  cardinality, and any many-to-many matches or row expansion. Record how the
  executed join handles missing keys and duplicates.
- Matched and unmatched counts on each side at that stage, distinguishing
  rows from distinct keys and input matches from output rows. Give each
  denominator and rate calculation explicitly; use the corresponding side
  and unit, since duplicates and many-to-many joins can multiply output rows.
  Label unavailable counts and the evidence needed to measure them.
- A traceable sample of unmatched keys from each side, with its selection
  method, and evidence about encoding, quote characters, whitespace, and
  case. Preserve literal values in an inspectable representation. Check
  these as possible explanations, not as permission to normalize keys or
  assume a cause from an unmatched count.

Trace join-introduced missingness and row duplication or loss into subsequent
operations, constructed variables, and estimation samples. Record where a
missing value first appears, how the code handles it, and which downstream
sample rules retain or exclude the affected observations. Missingness may
also predate the join; keep that distinction in the evidence.

## Construction and sample-rule audit

Compare each relevant constructed variable definition and sample rule in the
paper's text, table/figure notes, footnotes, appendices, and code. Follow the
actual sequence of operations: transformations, aggregation inputs and
weights, missing-value handling, filters, and final estimation-sample
exclusions. Trace missingness created or propagated by each construction,
including how aggregation and downstream sample selection handle it.

Use one evidence row per definition or rule, splitting conflicting source
claims into separate rows when needed:

| Variable or sample rule / scope | Text definition and source anchor | Notes/appendix definition and source anchor | Code construction or filter and source anchor | Observed construction, missingness, and downstream sample evidence | Agreement, anomaly, or unresolved coverage / next evidence |
|---|---|---|---|---|---|
| `<name or rule; scope ID if declared>` | `<definition; page/section>` | `<definition; note/page, or unavailable>` | `<operations; path:lines>` | `<stage; log/output anchors; counts and denominators where measured>` | `<comparison; conflicting sources; gap and next evidence>` |

A contradiction is a sourced anomaly, not automatically a coding error.
Preserve the competing text, note, and code evidence, distinguish observation
from a diagnosed cause, and state what remains unresolved. A missing source
or inaccessible stage stays a named coverage gap rather than agreement.

## Preservation, authority, and reporting

Author package files remain read-only under the skill's existing hash rules.
Preserve the original run's outputs, logs, comparisons, and code/input/
environment identifiers before diagnosis or correction. Put checker scripts
and fixes in new files; retain corrected runs as separately labelled results
with their changes and reasons. They cannot overwrite the original outcome or
widen its printed-digit comparison tolerance.

Log anomalies for the existing `probe` candidate inventory, with evidence and
unresolved interpretations. Candidate corrections that change a variable,
sample, or other specification follow the existing author-ruling and
[plan-approval requirements](probe-approval.md) before execution; the audit grants no new
specification or approval authority.

Report completed audits, unexamined joins/constructions, unavailable evidence,
and unresolved anomalies separately in `reproduce/README.md` and the report.
Derive canonical ACRe criteria, selected-target categories, and whole-paper
categories under `assessment.md` and `rules.md` unchanged. Audit coverage is
not an additional condition for Fully or another category, and does not
change output scope or comparison tolerance.
