# Report presentation and disclosure

Apply this contract at every cumulative build under `cumulative-report.md`.
The selected I4R template governs format; `assessment.md` governs categories
and evidence. Presentation adds no category, execution, or publication authority.

## Captions and context

Caption every table and figure, including checklists and the causal graph.
Number report tables R1, R2, and so on; in LaTeX use
`\renewcommand{\thetable}{R\arabic{table}}`. Refer to a source table as
“article Table n” (or “article SI Table n”), and to a report table by its
label. Never leave “Table 1” ambiguous between the article and this report.
Replace contextless phrases such as “in the template” with the named I4R
template, section, and relevant requirement. Before each numeric comparison,
state the substantive effect in plain words: what changes, for whom, and
relative to which comparison. Then give the target and numerical evidence.

Caption the six-row summary **Reproducibility Table**, with its whole-paper
or selected-target scope. This name follows the Brodeur-derived rule 1 in
`rules.md`; the committed I4R templates leave this table uncaptained, so an
official universal I4R caption is unverified. Credit Institute for Replication
for the selected template and state this naming provenance in a note.
“Computational reproducibility of the main claims” captions the separate
detailed comparison table in those templates; it is not evidence for naming
the six-row summary. Retain all six derived rows and their reasons.

When evidence has been examined but the assessor hesitates between categories,
put `?` in each candidate category cell and explain the unresolved choice in
the row note. This is a display of hesitation, never an asserted category or
a change to `assessment.json`. Reconcile the dossier before asserting a category.
Unexamined coverage or an unexecuted computation instead has explicit
“not yet assessed” or “not yet assessed — not yet run”, respectively, plus
its reason; leave its category cells unmarked and place that status beside
the row. Neither missing execution nor a blocker licenses candidate categories.
Retain independently verified provision-based impossibility with its distinct
basis under `assessment.md`.

## Documentation checklist

Keep the selected template's documentation checklist rows verbatim:

- README document
- Data dictionary
- How to obtain data not present in the replication package (if applicable)
- Documentation for primary collected surveys or experimental data (if applicable)
- Code execution instructions
- Computational requirements: libraries/packages, running time

Retain its columns “Provided and clear”, “Provided but unclear”, and
“Not provided”; derive entries from the inspected package, never the template's
illustrative marks. Add immediately below the computational-requirements row:
“Provides a ready-to-run environment (container image or lockfile)”, visibly
marked “Addition by the replication team”. This added checklist item is
separate from the six-row assessment and changes no schema or score.
State whether package versions are listed, distinguishing author-provided
versions from versions observed in the reproduction environment. Record their
source, missing versions, and whether the image/lockfile was actually used;
file presence alone does not prove a successful run.

## Robustness presentation

Keep the heading **Robustness Reproduction**. Open with: “Robustness
Reproduction examines the same data under alternative analytical decisions.”
Explain the actual alternatives and their relation to the main result.
Separate any replication with new data under its own applicable template
section. Existing signed-plan and execution boundaries remain binding.

A check omitted from the new challenge because the article or SI already
reports it needs a label cross-reference to its reproduction evidence in
Computational Reproducibility. Say it was reproduced only if execution
supports that statement; otherwise identify its reported source, not-run
status, and reason. An article's reported check is not a completed team check.

Give counts of signed checks, run checks, and not-run checks from the plan's
stable check IDs and execution/disposition records, with the counted unit and
scope explicit. For the signed set, reconcile signed = run + not run;
failed runs count as run and retain failure evidence. Identify unsigned
proposals separately. List each not-run check with its reason; preserve
withdrawn, blocked, adverse, and inconclusive dispositions and amendments.
Do not substitute counts of statistics or model calls for counts of checks.

Report in-frame and out-of-frame checks separately, with stable plan IDs,
the main claim/estimand and the reason for that classification. “Out-of-frame”
needs an actual change of analytical frame or discriminating implication;
a method's label alone is insufficient. Put each result beside the original
estimate when comparable, explaining changed estimands, nulls, or units and
unavailable comparators. Preserve actual approval, execution and result
dispositions, including failed/blocked/withdrawn checks and unavailable evidence.
An infeasible outside-frame proposal remains an unmet obligation with its
reason and search for a fair alternative; it is never reported as run or met.

“Signed” counts include every valid approval mode in `probe-approval.md`,
including source-bearing author approval transcriptions and bounded delegated
panel decisions, with their conditions fulfilled. A literal Signed-off-by line
is not required for those modes; an agent's invented signature is never valid.
Keep proposed, approved, run, and not-run states distinguishable; approval of a
plan supplies no additional outward or spending permission.

## Signature and AI Disclosure

Use “Auto-generated by <model>, guided by <user>”, substituting the actual
observed generating model and named guide. If model identity is unavailable,
say “model identity unavailable”; retain any requested model separately.
A requested pin or assistant self-report is not observed served identity.

Collect disclosure evidence from inventory onward in existing README/report
records, then finalize it at complete. Give the project repository and commit,
and the harness repository and commit, including the skill version used.
For MOE, team leads, coders, and reviewers, record observed model identity,
number of calls, and share of work with the collection source and period.
Distinguish roles unused in this run from roles whose historical evidence is
unavailable. Define each measured work-share denominator and method; calls
alone do not measure intellectual contribution. Report unavailable counts or
shares as unavailable, never zero or invented percentages. Preserve masked
identity, partial logging, reviewer independence limits, and source/exposure
boundaries. Stage updates retain gaps rather than reconstructing fictitious
history. Local disclosure supplies no authority to publish or contact anyone.
