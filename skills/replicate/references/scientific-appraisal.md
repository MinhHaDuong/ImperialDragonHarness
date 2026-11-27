# Computational and scientific reproduction

Hold two questions together for the declared main claim: does the executed
implementation reproduce the reported specification and outputs, and does the
argument, model, and factual evidence support the scientific conclusion?
Keep the answers distinguishable. Numerical agreement cannot certify the
scientific argument; scientific plausibility cannot erase a computational miss.

## Bound the appraisal and retain its sources

Start with the original-paper claim selected under `main-result.md`, its
supporting argument/model, and material factual premises. State the appraisal
coverage, source versions, and whole-paper or selected scope, including any
difference from the execution perimeter. Do not expand a selected run or claim
whole-paper scientific coverage from one result. Inspect material links needed
to assess the declared claim; this is no mandate to perform every conceivable
audit or verify every cited fact. Unavailable sources and unexamined links
remain named gaps, with the evidence needed to assess them.

Work sequentially: declare the claim and premises, link available evidence,
then argue the conclusions. Maintain a compact record in the host folder's
existing README/report evidence, with page, passage, code, or output anchors:

| Record | Evidence to retain |
|---|---|
| Original scientific claim | Original passage/version, supporting result, scope, and interpretation claimed by the authors. |
| Argument and model | Premises and assumptions connecting observations or estimates to the claim; what the model represents and what it leaves unresolved. |
| Material source facts | What the paper reports, what was actually checked and how, conflicting evidence, and unavailable or unexamined sources. A reported fact is not automatically independently verified. |
| Implementation and specification | Executed code/input/environment identifiers, model/sample/construction choices, comparison evidence, and unresolved text/code differences. Record unavailable execution explicitly. |
| Appraisal and disagreement | Claim-specific reasoning linking the evidence to separate computational and scientific conclusions; reviewer disagreement and its effect on the argument. |
| Next evidence | Missing sources, questions, and proposed checks with their status and approval boundary. |

Label source-reported facts, verified observations, reviewer inferences,
unknowns, and unexecuted proposals explicitly. Source assertions and agreement
between sources alone establish no independent verification. Preserve conflicting
sources rather than choosing whichever makes the paper easier to confirm or reject.

## Connect the existing audits to the scientific argument

Reuse `data-audit.md` construction, sample, join, and missingness evidence.
Trace any material text/notes/code anomaly to the premise or model component
it could affect. Preserve the observed contradiction separately from its cause
and possible scientific consequence; a contradiction alone establishes neither
a coding error nor failure of the claim. Conversely, matching code and text
does not establish that the chosen measurement or model supports the claim.

For causal claims, use `identification-review.md` for the estimand, sourced DAG,
assumptions, and argued reviewer judgment, including its distinct-perspective
requirements. Connect identification to the factual premises and implementation;
a passed diagnostic or computational match does not establish identification.

For descriptive or predictive claims, appraise the relevant measurement,
population/sample, model assumptions, uncertainty, and claimed generalization
or transport. A prediction match need not justify a causal interpretation.
Use the argument appropriate to the claim; do not impose a causal DAG or causal
identification label on noncausal work. Mixed papers require the appropriate
appraisal for each material claim, with their scope visible.

For meta-analysis, trace material links among eligibility, included studies,
extracted effects and definitions, overlap/dependence, pooling assumptions,
and the synthesis claim. State which links were inspected and what remains
unknown. Matching a pooled result alone cannot settle selection or dependence.
This appraisal requires neither universal study re-extraction nor new pooled
estimates; proposed calculations remain subject to existing approval.

## Diagnose a discrepancy and its scientific impact

Preserve the original computational observation before explaining it: authoritative
printed target and source version, full-precision output, comparison rule, status,
and code/input/environment identifiers. Keep first-run freezes and their hashes.
The half-unit-of-the-last-printed-digit tolerance and original classification
remain fixed. Retain subsequent diagnoses and any corrected runs as separately
labelled evidence, linked to that observation, without overwriting it. Apply this
distinction to whole-paper and selected-target work alike.

For each discrepancy material to the appraisal, extend the existing claim-to-evidence
record with two separate judgments:

| Judgment | Required evidence and limits |
|---|---|
| Cause | Name the observed difference, candidate explanation, inspected source/code/output anchors, and evidence that distinguishes that explanation from alternatives. A source correction or erratum can document a typo; retain its version and show which printed entry it corrects. A suspected typo stays inferred. Numerical variation needs evidence tying the difference to the actual implementation/environment or numerical mechanism under comparison; small magnitude or a familiar software difference alone establishes no cause. Record an unestablished cause as unknown. |
| Scientific impact | Trace the diagnosed difference to the declared claim and its supporting evidence: direction, magnitude or interpretation, uncertainty, decision boundaries, and affected premises as relevant. State what was actually checked, what follows by inference, what remains unknown, and the coverage of the conclusion. A demonstrated cause alone establishes no harmlessness: a documented typo may still change a material conclusion. |

A documented typo or demonstrated numerical variation can support the argued
conclusion “scientific result confirmed despite computational discrepancy” when
the evidence establishes the cause and supports the declared scientific claim
despite that difference. Retain the miss, its counts, and the computational
classification beside that conclusion. Unexamined material links still limit
coverage; confirmation of one claim establishes no whole-paper scientific verdict.
An unexplained small delta remains unexplained, with its scientific effect
unresolved where the missing diagnosis matters. Size alone supplies no harmlessness
exemption. A small difference can cross a material decision boundary; conversely,
a computational match can coexist with a scientific concern.

Use available authorized evidence for this diagnosis. If establishing cause or
impact needs a new empirical diagnostic, corrected estimate, model, or specification,
record the proposed check and its approval status under `probe-approval.md` and
the existing specification rulings. Execute only when existing approval explicitly
covers it; this reference grants no new run authority. Ordinary faithful
path/environment repairs remain under rerun's existing preservation rules;
appraisal-driven empirical/specification changes require approval. Preserve adverse,
inconclusive, and conflicting evidence under the same scrutiny as favorable evidence.

Report these judgments in the existing README/report evidence, linked to the
frozen comparison rows. They introduce no CSV/schema field, tolerance change,
miss-to-match relabeling, automatic ACRe or six-row category promotion, or silent
legacy rescore. Historical outputs and classifications stay frozen; a later
appraisal is a separately dated, sourced conclusion.

## Carry the two conclusions through the workflow

During `inventory`, record the original claim, source-based premises, inspected
facts, and gaps. During `identify`, appraise the argument/model and material
facts with targeted verified source checks, causal fidelity/credibility where
applicable, and appropriate noncausal reasoning otherwise. Run no estimates;
record premises needing literature support before publication. Deep literature
is separate. Computational outcomes remain unassessed before execution.
During `rerun`, connect executed specification and data-audit evidence to
that record, retaining first-run comparisons and subsequent diagnoses separately.
During `challenge`, derive fair proposals from material unresolved premises and
anomalies alongside existing candidates. A source-based appraisal runs no new
estimates: new empirical checks, corrections, and amendments await valid
approval under `probe-approval.md` and the existing specification rulings.

In every stage's compiled local report, present computational evidence/outcomes
separately from scientific
support, limitations, and disagreement, linking both to the claim-to-evidence
record. State whether the evidence supports the declared scientific claim,
limits it, contradicts a required premise, or leaves it underdetermined, with
reasons and remaining uncertainty. Preserve a computational discrepancy even
when the scientific argument appears plausible; retain a scientific concern
even when every compared number matches. Neither conclusion substitutes for
the other. No composite score, subjective probability, or autonomous scientific
certification follows. ACRe, comparison tolerances, assertion/auxiliary rules,
and six-row categories remain governed by `assessment.md` and `rules.md`.

Apply the same evidential scrutiny to favorable and adverse appraisals under
rule 4. Validation exposure and blind source exclusions govern all retrieval,
advisors, and review contexts under the skill and `validation.md`; missing
scientific evidence authorizes no excluded-source discovery. No new spending,
outward communication, publication, or plan-approval authority follows.
