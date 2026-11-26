# Causal identification review

Adapted from replicator's `doc/identification-method.md` at commit
`eded45754c76bd3d1822703e2cd0923a9237b8a4` (2026-11-26), developed for
Carter (2024), Figure 5. The source note attributes its prompts to Pearl
(2009), *Causality*; Pearl, Glymour, and Jewell (2016), *Causal Inference in
Statistics: A Primer*; and Cinelli, Forney, and Pearl (2022), “A crash course
in good and bad controls.” This adaptation retains its DAG conventions and
eleven prompts, generalizes the RDD examples, and replaces its probability-based
verdict definitions. The case's causal judgment supplies no verdict for
another paper.

## Scope and evidence

Write an **Identification** section within `report/`, alongside the
computational assessment. Declare the exact causal claim and estimand: the
treatment or exposure, outcome, population, comparison, and time horizon.
Reuse a selected-target scope ID when applicable and state any difference
between that numerical target and the causal claim reviewed.

Work sequentially: establish the claim, map the design, appraise the prompts,
then argue the judgment; each step supplies the next step's evidence. Use the
paper, supplements, published critiques, and reported tests with page, table,
or figure anchors. Distinguish what the authors claim, what critics claim,
and what the reviewers infer. Unavailable sources remain evidence gaps.

This review runs no new estimates. Put proposed empirical checks, including
sensitivity analyses or bounds, into the existing `probe` plan for a person's
signature before execution. Keep causal identification distinct from
statistical significance and estimator robustness: a precise estimate or
stability across specifications alone cannot establish a causal interpretation.
ACRe and all six Reproducibility Table rows assess computation only; never
feed these judgments into their categories, criteria, or statuses.

## Map the design with a DAG

A directed acyclic graph (DAG) maps the assumed causal relationships. An
arrow A → B says that A can change B; a missing arrow excludes a direct
causal effect in this model, while indirect paths may remain.

| Mark | Meaning |
|---|---|
| Rectangle | Observed variable |
| Dashed rectangle | Unobserved variable |
| Bold arrow | Causal path claimed by the paper |
| Grey arrow | Path threatening that claim |
| Double border | Variable conditioned on through a control, sample restriction, or fixed effect |

Draw the design actually estimated, including treatment timing, selection,
and conditioning. For an RDD, include the running variable and threshold;
other designs need their own assignment mechanism. Use temporally distinct
nodes when feedback would otherwise create a cycle, explaining the time
ordering rather than silently deleting a relationship.

Give every node and arrow a source anchor and identify whose claim it is
(author, critic, or reviewer inference). Record the absent-arrow assumptions
that identification relies on, with their rationale and evidence limits;
an omitted arrow is an assumption, not evidence of absence. Keep competing
source-supported graphs visible when they imply different conclusions.

## Adapt the eleven prompts

These prompts guide appraisal; they are neither exhaustive nor a universal
test of identification. For each, record applicability and its reason, the
source-anchored evidence, whose claim is assessed, a reasoned finding, and
remaining uncertainty. For every applicable item, write two plain-language
explanatory sentences: first the economic story, then why the evidence or
assumption matters for the stated causal claim. Introduce technical terms
after that explanation.

Use findings such as **no supported threat under the stated design**,
**examined in a reported test**, **open**, or **present**, with an argument.
“Not applicable” needs a design-based reason. A reported test describes what
was examined; its existence alone does not resolve the threat. State its
observable implication, result, detectable alternatives, and power or
precision where reported; unavailable power stays unknown.

Core identifying assumptions can be untestable. Separate source evidence
about testable implications from argued support for untestable assumptions.
A passed diagnostic or failure to reject its null cannot establish those
assumptions; a favorable test result remains evidence within its limits.

1. **Confounding.** Could a common cause of treatment and outcome leave an
   open path between them? Name that cause, the path, and the design feature
   or assumption that would block it, including relevant unobserved causes.
2. **Confounding versus association with treatment.** Does an observed
   treatment-group difference also affect the outcome through an open path?
   Adapt this to the actual comparison: an RDD needs continuity arguments at
   its cutoff, while a geographic border can coincide with an administrative
   change. Smoothness of one variable alone establishes neither continuity
   of all potential outcomes nor absorption of other causes.
3. **Which arm of the confounding path the evidence supports.** Separate
   evidence linking the candidate cause to treatment assignment from evidence
   linking it to the outcome; then assess whether the design leaves that
   path open. A pre-treatment factor can affect an outcome measured later;
   the outcome's measurement date does not make the factor post-treatment.
   A difference caused by treatment itself needs a different causal account.
4. **Bad controls.** Does conditioning on a mediator or another consequence
   of treatment change the target effect or introduce bias? Explain whether
   the target is a total or direct effect and which assumptions justify the
   adjustment, rather than treating every mediator adjustment alike.
5. **Colliders and sample selection.** Can conditioning on inclusion,
   survival, response, or recording open a path through a common effect
   (a collider)? Show the relevant causes of selection and the conditioning
   actually performed, rather than inferring bias from selection alone.
6. **M-bias.** Does an adjusted pre-treatment variable share separate causes
   with treatment and outcome so that conditioning opens a path between
   them? Its timing alone does not make it a safe control; locate the
   proposed path in the graph and establish whether adjustment occurs.
7. **Table 2 fallacy.** Are coefficients on controls interpreted causally?
   Each such interpretation needs its own estimand and identification
   argument; an adjustment set for the treatment effect need not identify
   the effect of a control.
8. **Mechanism from two total effects.** Does evidence that treatment affects
   both an intermediate variable and the outcome establish the proposed
   mediation path? Consider other channels and the additional assumptions
   needed to identify a mechanism from those separate effects.
9. **Compound treatment and exclusion.** Does the coded treatment bundle
   changes beyond the intervention named in the claim? Distinguish a bundle
   effect from its components; where an instrument is used, appraise its
   exclusion restriction and other required assumptions explicitly.
10. **Treatment misclassification.** Can errors in exposure, assignment, or
    treatment coding change the comparison? In an RDD examine coding near
    the cutoff where relevant; elsewhere trace the error through that
    design's assignment and measurement process without assuming a direction
    or size of bias.
11. **Interference and sorting.** Can treatment spill over to other units,
    or can units select their assignment? Appraise each separately, with
    design-specific implications: sorting around an RDD cutoff is one
    example, not a requirement for every design. State the resulting limits
    on the treatment definition, comparison, and population.

Add design-specific assumptions these prompts do not cover; for example,
parallel trends in a difference-in-differences design or instrument relevance
in an instrumental-variables design. Cite any existing sensitivity evidence,
state what it bounds under which assumptions, and leave a proposed new
calculation to the signed `probe` plan.

## Give an argued reviewer judgment

Before the judgment, explain which unresolved assumptions and threats matter
most for the declared claim, which source evidence supports them, and which
remain untestable or undocumented. Seek a different-family perspective for
substantive causal reasoning through the route skill. Preserve disagreements
and disclose an unavailable perspective; another same-family pass provides
replication of review, not lineage independence.

Use the following labels only with a claim-specific argument:

| Reviewer judgment | Meaning |
|---|---|
| **Well identified** | The design supplies a coherent identification argument, the main assumptions have argued support, and the available evidence leaves no material unresolved threat. State any untestable assumptions and the limits of reported diagnostics. |
| **Plausibly identified** | The causal interpretation has an argued basis, but a material unresolved assumption or threat keeps the conclusion provisional. Explain why the available support warrants that judgment despite the gap. |
| **Weakly identified** | The identification argument has material gaps or threats that substantially limit support for the claimed causal interpretation. Explain what remains defensible and what the evidence cannot settle. |
| **Not identified** | The stated design and assumptions do not identify the declared causal claim, or the evidence establishes a failure of a required identifying condition. Specify the failed argument; this does not establish that the true effect is zero. |

These are argued reviewer judgments, not standardized certifications,
reproducibility statuses, or technical weak-identification diagnostics such
as weak-instrument diagnostics. Record any such technical diagnostic
separately under its actual definition. When the sources cannot support a
label, say **underdetermined**, name the missing evidence, and explain what
would permit judgment. Do not force a label or generate subjective
probabilities or percentages.

End with evidence that would strengthen or weaken the judgment and questions
for the original authors; do not send them. Apply the same evidential standard
to favorable and adverse conclusions, following rule 4 in `rules.md`. Preserve
the DAG, source map, checklist, and judgment with the report so that a reader
can trace each conclusion without rerunning an estimate.
