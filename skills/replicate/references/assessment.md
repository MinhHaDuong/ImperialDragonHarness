# Assessment, manifest and output schemas

The replication's scored state uses `assessment.json`, `manifest.json`, and
comparison CSVs (`out/reproduce.csv`, `out/robustness.csv`). The six-row
Reproducibility Table and ACRe level are derived under the rules below;
neither is entered by hand. Separate `out/auxiliary.csv` estimates provide
provenance, never comparison statuses or scoring inputs. Published ranges and
inequalities have separate assertion evidence under § Published assertions;
assertion confirmation does not supply an exact statistic match.

## assessment.json

The vocabulary is the CIRED grid's (`grille-i4r.json`, id `acre-i4r-1`, in
the CIRED reproducible-science project, `monitoring/`). It adapts the
ACRe ten-level scale (<https://bitss.github.io/ACRE/assessment.html>) used in
the I4R study (<https://doi.org/10.1038/s41586-026-10251-x>).

```json
{
  "schema": "replicate-assessment-1",
  "grid": "acre-i4r-1",
  "citekey": "gavard2026climate",
  "main_result": "Table 1, joint model, six-lag sums (chosen before any run)",
  "criteres": {
    "analyse_partiellement_accessible": "Table 1 code and variables are present; appendix Tables A2-A3 lack sector inputs",
    "chaine_brute_incomplete": "the raw chain stops at the panel: neither CRS records nor cleaning code",
    "code_nettoyage_inaccessible": "package inventory and script inspection found no cleaning transformations for any applicable path"
  },
  "non_etabli": {"donnees_brutes_completes": "CRS activity records not in the deposit"},
  "a_evaluer": ["cra_reussie", "cra_echouee", "crr_reussie", "crr_echouee"]
}
```

This excerpt illustrates evidence fields; expand the criterion dossier from
the named grid before saving an actual assessment. It records partial analysis inputs for the paper, even though
Table 1 can be attempted. Derive its level with the grid; Table 1 evidence
alone establishes neither whole-package completeness nor a successful run.
The derived `level` and `history` fields are omitted from this illustration;
fill them only after computing the level with the grid.

- **`criteres`** holds only the criteria that are established, each mapped to
  one verified piece of evidence (path and line, URL and passage, or CSV
  row). Its shape is the dossier of the CIRED `classer.py --preuves` option,
  so the export is mechanical:
  `{"<citekey>": {"criteres": <criteres>}}`.
- **`non_etabli`** maps each criterion that was examined but not established
  to the reason. A missing piece and a failure are both evidence.
- **`a_evaluer`** lists criteria not yet examined, including run criteria
  until execution evidence exists in `rerun`. Every grid criterion belongs to exactly one of
  `criteres`, `non_etabli`, or `a_evaluer`; enumerate them from the named grid.
  Never use an undocumented empty `criteres` as the assessment.
- **`blocked`** maps unexamined criterion IDs to an access or evidence reason,
  attempted source, and next step, for example
  `{"donnees_brutes_completes": {"reason": "archive login required",
  "source": "<package URL>", "next_step": "logged-in download into data/"}}`.
  Keep these IDs in `a_evaluer`, never in `non_etabli` merely because access
  failed. Add `paper` or `package` entries for shared blockers; identify the
  affected criteria too. An unseen package leaves all content-dependent
  criteria unexamined. An unseen paper leaves `main_result` null with a
  `paper` blocker until an authoritative original-paper excerpt supports the
  choice. Inspected package facts can remain established, but unavailable
  whole-paper coverage cannot support any completeness criterion. A missing
  grid itself is a blocker to dossier completion and level derivation; report
  it explicitly rather than inventing criterion IDs.
- **A paper outside the grid's scope** (no empirical result) takes
  `"non_applicable": "<reason>"` instead of `criteres`, as in `classer.py`.
- **`level`** is the first rule of the grid, read from L10 down, whose
  criteria are all in `criteres`. With no rule matched, `level` is
  `non_etabli`; with nothing examined, `a_evaluer`. The rule is the one
  `classer.py` applies. Compute it with the grid file, never by eye:

```python
import json
GRID = "<path to grille-i4r.json, the grid named in assessment.json>"
grid, a = json.load(open(GRID)), json.load(open("assessment.json"))
rules = grid["dimensions"]["reproductibilite_calculatoire"]
examined = bool(a["criteres"] or a["non_etabli"])
level = (next((r["classe"] for r in rules
               if all(c in a["criteres"] for c in r["criteres"])), "non_etabli")
         if examined else "a_evaluer")
```

- **`history`** gets one entry per stage run that changed the level.
  `rerun` updates this same file. It never writes a second assessment.

## Package coverage and main-result runs

The current command chain is inventory → identify → rerun → challenge → complete.
Its execution-scope choice is recorded separately in README/report evidence:
main result, authoritative assignment-specific I4R perimeter, or whole paper.
It changes no schema, criterion, category, or selected-target contract below.
A main-only run leaves unexamined whole-paper execution coverage unresolved;
no-run rows display “not yet assessed — not yet run” with reasons, alongside any independently
established provision-based impossibility. Literal `stage=reproduce`,
`stage=robustness`, paths, and historical records remain unchanged.

Choose `main_result` under [Main-result choice](main-result.md), using the
original central claim before inspecting the package or executing code. Retain
the claim, supporting output, source/version, selection rationale, and any
advisor disagreement in `README.md`; `main_result` names that chosen output.
Package feasibility cannot choose or replace it.

The four completeness criteria cover the **whole paper**, including
applicable appendix and supplementary tables, figures, published robustness
outputs, and empirical footnote results under the applicability rule below.
The preselected `main_result` limits the ACRe run
criteria only. For package assessment, inventory the published outputs in
`README.md` and map each to its required files and code; carry that map into
`reproduce/README.md` when running. Identify outputs requiring no data or
code and explain their exclusion. Unexamined coverage stays `a_evaluer`.

| Criterion | Evidence required across the whole-paper inventory |
|---|---|
| `code_analyse_complet` | Analysis code for every applicable output |
| `donnees_analyse_completes` | Deposited analysis inputs or inspected complete producer chains for every applicable output, under [Analysis inputs generated by shipped code](#analysis-inputs-generated-by-shipped-code) |
| `code_nettoyage_complet` | Cleaning code for every applicable raw-to-analysis path |
| `donnees_brutes_completes` | Raw inputs for every applicable raw-to-analysis path |

Provision categories describe demonstrated coverage, not the extent of
inspection. Fully requires verified complete coverage of the applicable
whole-paper inventory. Partially requires both demonstrated provision and a
verified gap for that component: name the applicable output or path, the
provided files or operations, and the required missing item or stage. A
partial criterion records that evidence; its name alone does not establish
the category. No requires verified absence or inaccessibility of the entire
component under [The six-row table, derived](#the-six-row-table-derived).

An unknown inventory, an uninspected producer, or an unresolved boundary
establishes no gap. Leave the affected coverage unassessed and retain its
reason in `a_evaluer` and, where access or evidence is blocked, `blocked`.
Keep inspected files, inputs, and operations visible as lower-bound facts in
their established criteria (for example, `scripts_accessibles`) and the
coverage map; they alone establish neither Partially nor Fully. Finding the
chosen main result's inputs alone cannot establish whole-paper completeness.

A verified gap with demonstrated provision remains Partially even if another
output or stage is blocked or unexamined: the known gap already rules out
Fully. Name both the gap and the remaining unknowns. A blocker cannot create
Partially, erase a verified gap, or certify Fully or No; reconcile any blocker
that contradicts the evidence supporting the proposed category.

The run criteria refer to the main result. `cra_reussie` holds when every
statistic of the main result matches from the analysis data, and
`cra_echouee` when one does not. `crr_*` is the same check from the raw data.
The evidence is the path of the CSV and its rows' `outcome_key`.

### Empirical footnote applicability

Include applicable empirical results by meaning, regardless of whether they
appear in the body, a table/figure note, or a footnote. A footnote reporting
empirical evidence supporting a declared target belongs with that target's
required evidence; location alone cannot exclude it. For whole-paper coverage,
inspect such results across the paper. For a selected target, include the
applicable supporting footnote evidence within its declared perimeter; unrelated
results remain in the whole-paper inventory without expanding the selected run.
Retain the original main-result choice and canonical/selected scope distinction.

Record the authoritative version, passage/location, claim-to-target link,
required statistics or assertion, and computational applicability in the coverage
map. Trace applicable producers and inputs; distinguish missing code/data from
an absent numeric comparator and from an output requiring no computation.
Merely bibliographic remarks are not empirical targets. Record the reason for
an exclusion or unresolved applicability rather than converting an unexamined
footnote into complete coverage.

A printed numeric footnote result uses the existing comparison contract and
article tolerance. A sourced range or inequality uses § Published assertions,
with required endpoint comparisons retained. An unquantified assertion such as
“results are similar when these observations are excluded” supplies no numeric
comparator: retain its source and evidence limits, and apply the existing `challenge`
eligibility and approval rules for a check asserted without numbers or code.
Do not invent an estimate, numeric match, assertion predicate, or automatic
category from it. Produced estimates without exact comparators remain auxiliary;
actual failed/blocked attempts and unresolved coverage remain visible separately.

Carry these distinctions into README, the cumulative note draft, and the report,
including scoped omissions and unresolved claims. This prospective rule changes
no schema, comparison tolerance, or category derivation. Preserve old case
records; it authorizes no automatic inventory expansion, rerun, or rescore of them.

### Faithful Stata-to-Python CRA

When translation is authorized, a faithful Stata-to-Python reproduction from
analysis data is eligible for canonical `cra_reussie` under the existing
main-result scope and comparison rules. Verify the model, sample, standard
errors, and every required result; cite the inspected equivalence evidence
and comparison rows. Printed-value agreement alone or a source/port version
alone does not establish faithfulness. A missing equivalence check or
unresolved required comparison leaves success unestablished; preserve actual
mismatches and failed attempts under the existing outcome rules.

In `reproduce/README.md`, label the actual method as Python translation and
record native Stata execution status separately (not run, blocked, failed,
or completed, with evidence). Native execution is not a prerequisite for this
CRA route. Retain input representations and producer provenance, source and
port versions, locked execution environment, known differences, and unresolved
historical conventions. Apply [validation.md](validation.md) to exposure,
calibration choices, unused targets, and post-hoc changes; matching calibrated
outputs cannot settle an unknown historical convention.

This eligibility does not promote selected-target success to a different
`main_result` or whole-paper coverage. Keep all existing required comparisons,
printed-digit tolerances, and completeness criteria. It extends no CRR
eligibility and authorizes no automatic reassessment of legacy cases, changed
specification, or robustness execution. The author ruling is relayed in
ticket 1575 (reception commit `12e3c106b3980a972bedabca69802e136809ff9f`)
under B3; its implementation is ticket 1581.

### Analysis inputs generated by shipped code

Analysis-data provision can be Fully when the analysis files are absent but
inspection establishes a complete shipped producer chain for every required
analysis input across the whole-paper inventory. Cite the producing lines,
expected output paths and coverage, all required available inputs, and the
available software environment and dependencies. Record this basis under
`donnees_analyse_completes` as generated provision. A filename or an uninspected
producer is insufficient. A verified missing dictionary, input, or dependency
prevents this route to Fully. With demonstrated provision, record the known
gap under `analyse_partiellement_accessible`; otherwise leave unresolved
availability `a_evaluer` with its blocker. An uninspected dependency alone
is an inspection limit, not a verified missing dependency. Preserve separately
established code provision.
Do not infer successful execution from provision: before a run, `cra_*` and
`crr_*` and the execution rows remain unassessed. Execution later records the
observed result, including failed generation.

## Raw inputs and cleaning code

Raw data are the authors' deposited starting extracts for the documented
raw-to-analysis pipeline. Their provision does not require the entire
upstream archive, FOIA database, or source provider's database when the
extracts contain all inputs needed by that pipeline. Verify this boundary
against the documentation and transformations for every applicable path in
the whole-paper inventory. A deposited final analysis panel remains analysis
data; calling it the first available file does not establish raw provision.

Cleaning code comprises transformations that prepare analysis inputs,
including merges, recodes, lags, imputations, and sample construction. Count
these operations wherever they occur, including inside an analysis script.
Assess whether code covers each documented transformation from the starting
extracts to analysis inputs; a separate cleaning script is unnecessary.
Present cleaning operations with a missing panel-build stage establish
partial cleaning coverage, rather than total code inaccessibility.

Assess code provision separately from input availability and execution.
Complete cleaning scripts can establish `code_nettoyage_complet` while an
unavailable dictionary or input prevents complete raw provision or a run.
A script that writes no output needs execution diagnosis; that observation
alone establishes neither omitted code nor a partial code-provision row.
Record an established missing code stage, missing input, or execution defect
under its own evidence and affected component.

When inspection cannot resolve whether a supplied dataset is raw or
analysis data, record the ambiguity and its evidence separately from
provision coverage. Ambiguity alone leaves raw provision not yet assessed;
use `donnees_brutes_partielles` only for demonstrated raw provision with a
verified missing required input. For inseparable cleaning and analysis code,
retain the demonstrated cleaning operations as inspected facts. Establish
`chaine_brute_incomplete` for cleaning provision only when a required
cleaning stage is verified missing; unresolved coverage alone leaves that
row not yet assessed. The script's filename or separation into files does
not decide completeness.

These provision rules supersede the earlier ambiguity-only Partially
reading for raw data and cleaning code. Record the unresolved boundary in
`raw_analysis_boundary`, with `status: unresolved` and its inspected
`evidence`; retain the affected coverage and blockers separately. Boundary
uncertainty supplies no numerical execution outcome. Without comparison
outcomes or documented attempted-run failure evidence, both execution rows
remain not yet assessed, subject only to the verified provision-based
impossibility described in
[The six-row table, derived](#the-six-row-table-derived). Neither an
unresolved boundary nor that impossibility establishes `crr_reussie` or an
observed failed run.

## The six-row table, derived

The four provision rows use whole-paper package coverage; the two execution
rows use whole-paper reproduction coverage. Each row comes from the criteria,
the output inventory, and `out/reproduce.csv`. The grid has
no criterion for every "Partially" cell. There, the evidence text of
`analyse_partiellement_accessible` or `chaine_brute_incomplete` must name
which component has demonstrated provision and a verified gap, and the row
reads that evidence. Apply the provision interpretation in
[Package coverage and main-result runs](#package-coverage-and-main-result-runs)
to all four provision rows. Resolve coverage separately
for each component. No requires verified absence or inaccessibility of the
entire relevant component across applicable paths; a missing stage alongside
available cleaning operations is Partially. If evidence supports both a No
criterion and partial provision for the same component, reconcile the paths
and operations and correct the criterion dossier before deriving the row.
Do not resolve contradictory evidence by blanket precedence. A total absence
of cleaning code can coexist with `chaine_brute_incomplete` describing
available raw data: that evidence concerns different components.

| Row | Fully | Partially | No |
|---|---|---|---|
| Raw data provided | `donnees_brutes_completes` | `donnees_brutes_partielles` naming provided raw inputs and a verified missing input | `donnees_brutes_inaccessibles` or `aucune_donnee_accessible` |
| Cleaning code provided | `code_nettoyage_complet` | `chaine_brute_incomplete` naming present cleaning operations and a verified missing stage | `code_nettoyage_inaccessible` or `aucun_code_accessible` |
| Analysis data provided | `donnees_analyse_completes` | `analyse_partiellement_accessible` naming provided analysis inputs and a verified gap | `aucune_donnee_accessible` |
| Analysis code provided | `code_analyse_complet` | `analyse_partiellement_accessible` naming present analysis code and a verified gap | `aucun_code_accessible` |
| Reproducible from analysis data | every required statistic in the whole-paper inventory has a `stage=reproduce` analysis-data row with `status=match` | some required statistics match and others fail or have known missing inputs | none match, or the code does not run |
| Reproducible from raw data | same, for rows from raw data | same, based on raw-data comparison evidence | same observed-comparison rule, or verified provision-based impossibility as defined below |

Unresolved provision coverage yields "not yet assessed" unless demonstrated
provision and a verified gap already establish Partially for that component.
A blocker alone never supplies the gap. Blocked or wholly unexamined
execution evidence yields "not yet assessed" for each affected execution row.
In particular, zero CSV rows alone, inaccessible contents, or an
unavailable output inventory cannot establish No by the "none match" rule.
That reading requires examined coverage and evidence of failure or absence;
unknown inputs cannot establish the final-analysis-only exception in this section.

The execution rows require an inventory of all applicable outputs and their
required comparison statistics, mapped to `cra:` or `crr:` rows separately.
Record known missing inputs or failed attempts as `missing_input` or
`not_run` with the reason. An all-match subset earns no Fully: if inventory
coverage or any required comparison remains unexamined, print "not yet
assessed" and name the gap. Known missing inputs with some matches yield
Partially even when every executed comparison matched. Thus `cra_reussie`
for the selected main result can coexist with a Partially or not yet assessed
whole-paper execution row.

A provision row supported only by inspected lower bounds or unresolved
coverage is printed as "not yet assessed", with its facts and unknowns kept
visible. The verified-gap rule applies even when other criteria remain
`a_evaluer`.

Keep the basis of each execution category explicit in the row's evidence.
An observed-comparison basis cites the required outcome keys, comparison
rows, and run or failure records. An unresolved raw/analysis boundary alone
never establishes numerical Partially, Fully, or No. Without comparison
outcomes or documented failed attempts, print not yet assessed unless the
provision-based exception applies. A run that fails before producing numbers
can support No on observed failure: record the failed attempt, its log, and
`not_run` outcomes with reasons for the required comparisons under the
declared coverage rules. Zero attempted runs and zero matching outcomes
are different evidence states. Boundary uncertainty cannot override the
declared comparison-coverage rules or turn an unexamined
comparison into an observed failure.

The provision-based exception is a verified impossibility of a from-raw run:
inspection establishes that the package starts only at final analysis data
and supplies no required raw-data/cleaning path. Record the verified
boundary, missing raw inputs or cleaning code, and why no raw run is
possible. The from-raw row may then be No, explicitly labelled
**provision-based impossibility**, even without a run. This is distinct from
**observed failure** after an attempted run or examined nonmatching
comparisons. Mere failed access, an unknown boundary, an unexamined path, or
a missing raw-run CSV does not establish impossibility. Do not mark
`crr_echouee` from this inspection-only basis; run criteria retain their
main-result execution evidence requirements.

In the cumulative note draft and reports, show all six derived rows, including
Fully and not yet assessed, with the evidence basis and unresolved coverage
visible. Use the status "not yet assessed" for an unassessed row; append "not yet run"
and its reason when execution has not occurred. This is a display clarification,
not a new stored status or category. For unknown provision keep "not yet assessed";
if a fixed template offers only Fully/Partially/No columns, leave those
columns unmarked for that row and state the unassessed status and reason
beside it. The instruction to show only discrepancies applies to the
detailed statistic comparisons, not to this six-row status table.

## Selected-target assessment

This is an additive mode only on an explicit caller request. Whole-paper
assessment remains the default, including for Games. The existing
`criteres`, `non_etabli`, `a_evaluer`, `blocked`, `level`, and `history`
retain their canonical meanings. Keep the whole-paper table visible, including
unknown rows; a selected assessment does not require completing that audit
before proceeding. Do not migrate or rescore old evidence implicitly.
An explicit selected target need not be the canonical `main_result`; preserve
both declarations and their reasons under [Main-result choice](main-result.md).

Store the additional result in `assessment.json` under `selected_target`,
separate from every canonical grid criterion. A minimal declaration is:

```json
{
  "selected_target": {
    "scope_id": "fig5a-5d-numerical-v1",
    "mode": "selected",
    "declared_before": "dependency inspection and execution",
    "paper_evidence": "<original paper passage and exact version>",
    "outputs": ["Figure 5a", "Figure 5d"],
    "target_kind": "numerical",
    "required_outcomes": ["cra:fig5a.estimate", "cra:fig5d.estimate"],
    "exclusions": ["<other published outputs, with scope reason>"],
    "coverage_map": "README.md#selected-target-inputs",
    "provision": {},
    "execution": {},
    "reference_comparison": null
  }
}
```

The example's outcome list illustrates the shape; enumerate every required
statistic for the actual target and each requested analysis/raw route before
execution, including uncertainty statistics when required. The declaration
names the claim/output/estimate, original-paper authority, exact included
panels, models, samples, and statistics, and whether it assesses numerical
values or literal rendering. Record when and why it was chosen. If no
authoritative paper evidence supports the requested selection, record a
selected-target blocker and leave its categories unassessed. An unavailable
whole-paper inventory alone need not block a verifiable selected target.

The stable `scope_id` identifies the full declaration, rather than just a
figure title. Carry it through README, manifest input bindings, fetch/input
representation records, producer/consumer map, run logs, CSV outcome mapping,
selected rows, and report. Manifest bindings associate the scope with the
existing `files[].path` and exact `representation`, without changing checksum
semantics or pretending archive metadata are observed bytes. Shared files can
serve several scopes. An explicit outcome-key map to the unchanged CSV schema
suffices; do not silently reassign old rows to a different target. Record the
package version and inspected source lines in the dependency map. Include
transitive inputs required by the selected producer chain even when their
filenames or source datasets also serve excluded outputs. Exclude a dependency
only with evidence that the selected path does not consume it.

Changing included outcomes, target kind, package/input representation, or
a dependency boundary requires a new scope revision and a dated reason.
Preserve the earlier declaration and observations; reassess affected provision,
execution coverage, and reference comparisons before reporting current results.
Unchanged evidence can be reused only with an explicit mapping to the revised
scope. A still-valid selected run is resumable; unchanged bytes alone do not
validate a changed target. Record scope changes even if the canonical level
does not change. Historical dossiers without this namespace retain their
original whole-paper interpretation; a new scope is an addition with provenance,
not a relabelling of their observations.

### Provision, execution, and canonical separation

`provision` holds the four labelled component rows (raw data, cleaning code,
analysis data, and analysis code); `execution` holds the two labelled analysis
and raw reproduction rows. Each row records `status` (Fully, Partially, No,
or the literal `not yet assessed`), evidence, required coverage, and unresolved
items/blockers. Execution also names its basis: observed comparisons,
observed failed attempt, or provision-based impossibility. These are selected
row categories, **not new criterion IDs**. Never merge them into `criteres`,
export them through `classer.py`, or use them to elevate the canonical `level`.
Derive them from the declared inventory and evidence using the existing
six-row rules with the selected inventory replacing whole-paper coverage.

For each provision component, Fully requires verified complete target coverage;
Partially requires demonstrated provision and a verified required gap; No
requires verified absence or inaccessibility of the entire relevant component
across the selected paths. Inspected lower bounds with unknown required
coverage remain not yet assessed. A verified in-target gap survives unrelated
unknowns. A gap needed only for an excluded output cannot downgrade a selected
row; preserve it in the whole-paper audit with its actual output/path. An
uninspected producer or unresolved raw boundary creates no verified gap.

Retain separate evidence for information provision and software readiness.
Deposited, inspected analytic inputs remain provided when the execution
environment is unavailable; record that execution blocker separately. Likewise,
complete supplied code can remain provided when its interpreter cannot run.
When analysis inputs exist only through a shipped producer, retain all the
existing inspected-chain requirements, including available inputs, software,
and dependencies: an unverified producer cannot establish Fully generated
provision. Name missing inputs, missing code stages, and unavailable software
under their affected components; software failure alone proves no code omission.

Derive selected execution against every declared required comparison, separately
for CRA and CRR, with the unchanged printed-digit tolerance. An all-match subset
with unresolved required comparisons remains not yet assessed. Some matches
and verified required missing inputs follow the existing Partially rule.
Unresolved upstream raw provenance does not by itself block CRA from adequate
analytic inputs; it leaves raw-completeness and CRR claims unresolved unless
separate evidence settles them. Preserve the distinction between an observed
failed run and verified provision-based raw impossibility; inspection alone
never establishes `crr_echouee`. Canonical `cra_*`/`crr_*` still refer to the
original `main_result` and require their own appropriate execution evidence.

A numerical target concerns the specified estimates/statistics. Literal
rendering additionally concerns the declared graphics or document output and
its required assets. Missing rendering-only assets cannot become a numerical
gap without a dependency link; numerical agreement does not certify rendering.
Do not invent original printed numerical values from reproduced values for an
accuracy comparison. If the target has no authoritative exact numerical comparator,
retain the obtained numbers as reproduction facts and leave exact numerical
accuracy unassessed. An authoritative range or inequality can separately be
evaluated under § Published assertions; its confirmation cannot establish a
selected execution category alone.
No scope declaration changes tolerance or authorizes an adaptation convention.

### Reference comparison

Record reference source/version and passage, the literal printed categories,
and their documented scope separately from narrative interpretations or
conditional entailments. For each compared component, identify the selected
scope ID, reference outputs/statistics, numerical versus rendering target,
provision versus execution meaning, and category evidence basis. Reference
scope unavailable from the source stays unknown; an identical figure title or
category word does not establish equivalent scope.

Only scope-equivalent, evidence-supported categories may contribute to a
qualified agreement count, with numerator, denominator, excluded/unknown rows,
and any inference basis explicit. Different or unknown scopes cannot produce
an unqualified agreement score. A whole-paper printed Fully may support a
conditional selected-coverage implication only when inclusion and meanings
are verified; label the implication and its conditions, rather than treating
it as a directly printed selected category. Whole-paper Partially or No alone
does not locate a gap inside the target. Narrative inference remains distinct
from the printed label, and unknown reference rows never become agreements.

Show both six-row tables with explicit scope labels in the cumulative note draft and
reports. The canonical table retains whole-paper meanings; the selected table
names its scope ID and target kind, evidence basis, exclusions, and unknowns.
Report reference comparisons with those same qualifications.

## Comparison CSVs: out/reproduce.csv and out/robustness.csv

These columns map onto replicator's `replication_results` table. Write one
row per compared statistic. A coefficient and its SE are two rows: `t1.joint.adapt_l5` and
`t1.joint.adapt_l5.se`.

| Column | Content |
|---|---|
| `outcome_key` | table, column or model, and statistic; stable across reruns |
| `stage` | `reproduce` or `robustness` |
| `original_value` | as printed in the paper (or, in robustness rows, the reproduced original) |
| `reproduced_value` | full precision |
| `se` | the reproduced estimate's SE, empty for a row that is itself an SE |
| `p_value` | the reproduced estimate's p-value, where defined |
| `status` | `match`, `discrepancy`, `missing_input` or `not_run` |
| `spec` | `original` for reproduction rows, else the alteration's name from `robustness/plan.md` |

A row matches when the reproduced value lies within half a unit of the
paper's last printed digit. The source (`analysis` or `raw`) is the
`outcome_key` prefix `cra:` or `crr:` on reproduction rows. Keep every
row, matches included. The detailed statistic-comparison list in the report
shows only discrepancies and rounds to three digits; its six-row status
table remains complete, with evidence bases and unassessed rows visible.
This comparison display rule does not apply to retention of auxiliary rows.

Preserve original/frozen discrepancy rows and their classifications when later
evidence diagnoses their cause or scientific impact. Follow
`scientific-appraisal.md` § Diagnose a discrepancy and its scientific impact for
the separate evidence and conclusions. Scientific confirmation despite a retained
miss changes neither comparison counts nor the computational criteria/categories;
it authorizes no widened tolerance, automatic promotion, or legacy rescore.

## Comparing two reproductions

For two reproductions of the same declared statistic, agreement means numeric
equality after rounding both values to three significant digits by the following
common rule. This comparison is separate from paper comparison and from report
display. It supplies no additional canonical category or scope promotion.

Use the exact decimal value of each retained, unrounded input. For binary
floating-point inputs, use their exact decimal expansion, not an already rounded
printout; record the storage type and conversion method. Do not discard digits
before applying the rule. For a nonzero finite value `x`, find the integer `e`
such that `10^e <= abs(x) < 10^(e+1)`, and set `q = 10^(e-2)`. Round `x/q` to
the nearest integer, with exact halfway cases going away from zero, then multiply
by `q`. Apply the same rule to both inputs, including negative values. Compare
the rounded numbers, not their formatted strings. A carry can change the
exponent: `999.5` rounds to `1.00e3`. Exact zero rounds to zero; signed zeros
compare equal, with their original signs retained. Every nonzero finite value
uses its own magnitude, however small or large; no absolute epsilon applies.

Missing, unavailable, NaN, and infinite inputs do not establish numeric agreement,
even if both carry the same marker. Record the comparison as unresolved with a
reason; retain any available original and leave unavailable rounding/difference
fields empty. Compute a difference only when both originals are finite.

Retain a separate cross-reproduction ledger, such as
`out/cross-reproduction.csv`, with these fields for each comparison:

| Evidence | Content |
|---|---|
| Target and scope | Stable statistic/model identifier, main-result, whole-paper, or selected scope ID, and required-output inventory binding |
| Originals | Both unrounded values at full available precision, including original zero signs, storage types, and exact-decimal conversion method |
| Protocol and provenance | Both producer/source revisions, input artifacts and hashes, execution environments, known differences, and the common rounding/tie rule |
| Rounded values | Both three-significant-digit numbers, retaining trailing zeros or scientific notation to show precision |
| Difference | Signed second original minus first original, computed before rounding; retain its exact value or computation precision |
| Outcome | Agreement, disagreement, or unresolved, with reason and evidence pointers |

Keep this ledger distinct from article `match`/`discrepancy` totals and from
auxiliary unprinted estimates; neither port supplies an invented published
comparator. Agreement on a selected statistic does not establish whole-paper
coverage or canonical CRA/CRR. Article numeric comparisons retain half a unit
of the last printed digit, and published assertions retain their own predicate.
Report display still follows the three-digit display rule. Apply this convention
prospectively; preserve previous case records and disclose any explicitly
requested reassessment separately, without silently rescoring them.

## Published assertions

When the paper publishes a range or inequality, evaluate the actual sourced
assertion separately from exact statistic comparison. Record it in
`out/assertions.csv`, one row per declared assertion and executed route; bind
its stable identifier to the required-output inventory. This is an evidence
ledger, not an extension of the comparison CSV `status` vocabulary.

| Column | Content |
|---|---|
| `assertion_key` | Stable assertion identifier linked to the required-output inventory |
| `run_id`, `source_route`, `scope_id` | Run log, analysis/raw route, and declared scope |
| `source` | Authoritative paper version, location, and verbatim assertion |
| `target` | Exact quantity, units, object or collection, and any quantifier or extrema named by the source |
| `predicate` | Sourced inequality or interval, including each boundary's open/closed status; unresolved parts explicit |
| `evidence` | Produced full-precision values or artifact, producer, inputs, environment, and complete target-coverage evidence |
| `claim_status` | `confirmed`, `not_confirmed`, or `unresolved`, with reason |

Resolve the target before evaluating membership. For a scalar asserted to
lie in an interval, test that scalar against the sourced endpoints and their
inclusivity. For an inequality, preserve the operator: equality satisfies
`>=` but not `>`. Unknown inclusivity, units, target, or source meaning stays
`unresolved`; the typography of a dash alone cannot choose closed bounds.
Do not expand bounds by the article's half-unit tolerance, invent an exact
comparator or midpoint, or use reproduced values to fill missing source facts.

Preserve the assertion's quantifier and target kind. A claim about every
member of a named collection requires coverage of that collection; one
in-range member cannot confirm it. An existential assertion requires its
actual sourced existential meaning. An assertion about a minimum, maximum,
or reported range requires the corresponding extrema and coverage. If the
paper reports endpoint statistics, retain each required endpoint comparison;
checking that all reproduced values lie somewhere inside a band does not
establish those endpoint matches. For an interval object such as a confidence
interval, preserve the sourced relation (for example, containment or overlap)
and evaluate the whole object; testing its midpoint or one endpoint changes
the claim. Do not infer any of these meanings from a bare printed range.

Use `confirmed` only when the produced evidence establishes the complete
sourced assertion. Use `not_confirmed` when verified evidence contradicts it,
with the counterexample and coverage limits visible. Use `unresolved` when
meaning or required evidence is insufficient to decide; a missing input or
failed attempt retains its separate run/coverage disposition. Preserve all
three outcomes in the ledger and report, including unresolved required claims.

Report assertion totals separately from numeric `match`/`discrepancy` totals,
with denominators and unresolved coverage explicit. An assertion row never
receives a comparison `status` or supplies an exact match, and its confirmation
alone establishes no canonical ACRe criterion or six-row category. Keep every
required numeric target and its existing comparison outcome; an unexamined
required statistic stays unresolved. Produced quantities with no exact
comparator remain auxiliary under the next section, linked from assertion
evidence where relevant, without double-counting them as comparisons.

These rules implement the B6 author relay in ticket 1575 prospectively.
They authorize no silent reassessment of legacy cases, new estimates, changed
specification, or unapproved robustness execution.

## Auxiliary estimates

Retain produced estimates that lack an authoritative printed numeric
comparator in a separate `out/auxiliary.csv`, at full precision. They are not
comparison attempts or invented matches. Use this auxiliary contract rather
than the [comparison-column schema](#comparison-csvs-outreproducecsv-and-outrobustnesscsv):

| Column | Content |
|---|---|
| `auxiliary_key` | stable identifier for the produced estimate/statistic |
| `run_id` | identifier linking the row to its run log and provenance record |
| `producer` | script path and source lines/function producing the value |
| `spec` | exact specification identifier, resolved in the README |
| `source_route` | executed analysis/raw route; name any other actual route explicitly |
| `scope_id` | declared selected scope ID, or explicit whole-paper context |
| `statistic` | coefficient, SE, p-value, or other produced quantity, with units where relevant |
| `value` | produced value at full precision |

In `reproduce/README.md`, describe the auxiliary file and bind each run/spec
identifier to the actual producer/source version, inputs and representations,
locked environment, execution log, and model/sample/SE choices. Record why no
authoritative printed numeric comparator was available and the inspected
paper/source location supporting that statement. Use separate rows for
separate statistics or executed routes, preserving their scope provenance.
Do not invent a published comparator or copy comparison `status` labels into
this artifact. A blank auxiliary value cannot stand for a produced estimate.

Exclude auxiliary rows from `out/reproduce.csv`, match/discrepancy counts,
all comparison/score denominators, ACRe main-result criteria, and selected-target
scoring. Never aggregate all `out/*.csv` indiscriminately. An absent comparator
alone establishes neither `missing_input` nor execution failure; keep actual
failed or blocked attempts and their reasons in the existing run logs and
coverage/disposition records. A success-only auxiliary file cannot hide them.

Auxiliary retention does not remove required targets from the declared
inventory or resolve an unexamined/unavailable comparison. Apply the existing
scope and completeness rules, leaving unresolved required comparisons visible.
Published range/inequality evidence follows § Published assertions separately;
footnote inclusion follows § Empirical footnote applicability, independently of
auxiliary retention. Other qualitative claims retain their existing eligibility
and evidence boundaries; this contract settles no other comparator/tolerance question. Retain
only estimates produced under existing authority; this contract authorizes no new model
specification, translation eligibility, or unapproved robustness execution.

## manifest.json

The identity and provenance fields are shared with replicator's Phase B
`run.yaml`, so its pipeline can later take in a hand replication:

```json
{
  "doi": "10.1017/S1355770X26100679", "citekey": "gavard2026climate",
  "zotero_item": "<item key>", "family_id": null,
  "package": {"source_url": "https://zenodo.org/records/7149667", "version": "1",
              "retrieved": "2026-12-01", "language": "Stata"},
  "files": [{"path": "data/Final_panel_v6.dta",
             "representation": "original .dta",
             "archive_checksum": {"algorithm": "md5", "digest": "<listed digest>",
                                  "source": "<archive metadata URL>",
                                  "representation": "original .dta"},
             "sha256": null, "bytes": null,
             "license": "CC-BY-4.0", "redistributable": true}],
  "environment": {"interpreter": "Stata 18 MP", "lockfile": "reproduce/requirements.lock"},
  "template": {"name": "I4R Template: Reproduction Report – General", "record": "23226406",
               "version": "1", "reason": "no template named in the assignment; field fits none specific"}
}
```

`template` is added from inventory onward (chosen from `references/templates/INDEX.md`;
an adapted structure adds `"adapted": true`). Each file's `representation`
identifies the bytes requested (original format or archive-ingested `.tab`).
`archive_checksum` is nullable; when present it records the listed algorithm
(`md5` or `sha256`), digest, exact source URL, and representation it describes.
Top-level `sha256` and `bytes` are observed from the local acquired file,
not copied or inferred from archive metadata; keep them null until inspected
bytes exist. MD5 metadata alone proves no local download or integrity check.
Record transformations as separate representations, preserving source metadata.

### Caller-supplied private packages

`package.source_url` may be null when no downloadable source exists. A local
path or privately received attachment does not require a fabricated URL.
Retain `package.version` when known (otherwise null) and use `retrieved` for
the receipt date. Add acquisition evidence, for example:

```json
"package": {
  "source_url": null, "version": null, "retrieved": "2026-11-27",
  "language": "Stata",
  "acquisition": {
    "method": "caller_supplied",
    "evidence": "README.md#package-acquisition"
  }
}
```

The README acquisition record identifies who supplied the package, when and
how it was received, its original filename/representation, and the evidence
binding it to this paper/version. Mark unknown provenance or version facts
unknown. Use a provenance identifier permitted by the host's privacy rules;
receiving a private package grants no right to publish private correspondence.
The manifest's `files[].path` names the retained project copy; document the
local-path input interface for `fetch.sh` without requiring a workstation path
in the shared record.

For every retained file, compute `sha256` and `bytes` from the actual supplied
bytes and name that exact `representation`. For an archive-path input, record
the archive itself as a `files[]` representation before unpacking. Retain its
provenance and record extracted files as distinct representations;
an archive digest does not validate an extracted member's bytes. Keep
`archive_checksum` null when no applicable authoritative checksum is
available. Local hashes establish identity/integrity against those observed
bytes, not independent archive verification or package authenticity.
Preserve any known archive metadata separately under its stated representation.

Record licence and redistribution evidence for private bytes as for public
ones; unknown rights grant no redistribution. Caller supply authorizes local
intake within the assigned project, not author contact or outward publication.
Author files remain read-only. A blind assessment may use these explicitly
supplied bytes under the same source/answer exclusions as a supplied URL;
missing acquisition stays blocked and supplies no discovery authority.

### fetch.sh: public and local acquisition

Generated `fetch.sh` reads `files[]`. For a public source it requests the
recorded representation; the existing download route remains available. For
caller-supplied acquisition, document a local package-path argument or other
explicit input interface in `README.md`. Verify the supplied file's previously
recorded SHA-256 and byte count for that exact representation before accepting
or copying it into `data/`; verify the retained copy as well. Preserve original
bytes, and never edit the supplied source. Initial intake records the observed
digest/size before reuse; a mismatch on a later acquisition must not silently
replace that expected identity with a new hash.

A missing local path/file, unreadable bytes, or mismatch exits non-zero with a
clear required acquisition step. A later invocation without the original path
may verify and reuse an already retained exact copy; it cannot claim to have
reacquired a missing package. Do not fall back to discovery, author contact,
or a fabricated download URL. Exclude private bytes from redistribution
unless the recorded rights permit it.

For either route, `fetch.sh`
checks its applicable archive checksum and any previously observed local
SHA-256/byte count before accepting the file. A mismatch exits non-zero. A listed `.tab`
MD5 never validates the original `.dta` (or another original format): retrieve
the matching representation, obtain its own authoritative checksum, or record
that the archive check is unavailable for the original. Compute its local
SHA-256 and size when bytes are available, without claiming archive validation.
Blocked access exits non-zero with the access step needed; a login page is
never accepted as data. A successful metadata lookup alone leaves local
verification pending. Resume after access and refresh the affected blockers
and criteria as well as the local digest; valid unchanged evidence stays put.
