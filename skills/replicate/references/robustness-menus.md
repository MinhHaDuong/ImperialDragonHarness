# Design-specific candidate checks

Use after inventorying the paper, appendix, and code. These are candidates for
judgment, not required execution or permission to bypass the person-written
signature. Choose only fair additions and explain their applicability in the
paper's plan. Keep case variables, tuned thresholds, and unit choices there.
The binding scope and fairness rules remain in `rules.md`, especially rules
4, 5, and 7. Identification questions also enter through `identification-review.md`.

A check of the main model can be robustness; a new subgroup comparison is
heterogeneity, and a new question or population is an extension. Label the
latter two as extras even if a source calls them robustness. A sensitivity
analysis that changes the estimand must explain the change rather than claim
like-for-like confirmation. Diagnostic evidence alone does not prove an
identifying assumption.

## Meta-analysis

| Candidate | Applicability and limit | Inspected methods support |
|---|---|---|
| Publication-bias sensitivity | Consider a selection model over declared assumptions about missing studies/results. Funnel asymmetry alone does not establish publication bias; competing causes and model assumptions matter. | Page, Higgins, and Sterne, *Cochrane Handbook*, chapter 13, “Selection models” ([source](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-13)). |
| REML versus DerSimonian–Laird | For a random-effects synthesis, compare the between-study variance estimator while preserving the effect-size data and documenting inference choices. This comparison does not select a preferred answer by its p-value. | Deeks et al., *Cochrane Handbook*, chapter 10, §10.10.4, discusses both estimators and their performance ([source](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10)). |
| Drop-one study | Examine influence by refitting without each independent study. Account for dependent effects from the same study; extreme effects alone do not justify deletion from the final synthesis. | Viechtbauer and Cheung (2010), *Outlier and influence diagnostics for meta-analysis*, §4, case deletion, and discussion ([author copy](https://www.wvbauer.com/lib/exe/fetch.php/articles:viechtbauer2010b.pdf)). |

## Difference-in-differences

| Candidate | Applicability and limit | Inspected methods support |
|---|---|---|
| Threshold or dose definition | Where a continuous exposure was dichotomized, assess sensitivity to the definition and consider a continuous specification with justified identifying assumptions. Fix defensible alternatives before results. A new subgroup threshold is heterogeneity; changing treatment groups can change the estimand. The sources motivate this sensitivity question, not a universal cutoff grid. | Altman and Royston (2006), *The cost of dichotomising continuous variables* ([source](https://www.bmj.com/content/332/7549/1080.1)); Callaway, Goodman-Bacon, and Sant'Anna, *Difference-in-Differences with a Continuous Treatment*, introduction and §3, distinguishes dose effects and assumptions ([author draft](https://psantanna.com/files/CGBS_v4.pdf)). |
| Event-study specification | Examine event-time dynamics and pre-treatment differences using an estimator and aggregation appropriate to treatment timing/intensity. Failure to reject pre-trends does not prove parallel trends; new subgroup dynamics are extras. | Callaway, Goodman-Bacon, and Sant'Anna (2024), *Event-Studies with a Continuous Treatment*, sections I–II on group-time-dose parameters and aggregation ([author copy](https://psantanna.com/files/CGBS_AEAPP.pdf)). |
| Multiple testing over interactions | Declare the hypothesis family and error criterion before choosing a correction compatible with the dependence/design. Report adjusted inference beside the original; correcting new subgroup interactions does not make them main-model robustness. | Romano and Wolf (2007), *Control of generalized error rates in multiple testing*, introduction and stepdown procedures, distinguishes familywise and generalized error criteria ([paper](https://arxiv.org/pdf/0710.2258)). |

## Experiments

| Candidate | Applicability and limit | Inspected methods support |
|---|---|---|
| Pre-analysis-plan concordance | Compare registered hypotheses, outcomes, and specifications with the article and code; disclose deviations and assess feasible omitted planned analyses. Distinguish justified amendments from undisclosed changes. | Prasad et al. (2024), *A checklist to guide sensitivity analyses and replications of impact evaluations*, §4.5 and table 6, concordance with the pre-analysis plan ([source](https://doi.org/10.1080/19439342.2024.2318695)). |
| Alternative controls | Compare justified baseline covariate specifications, preserving assignment and inference. Exclude post-treatment controls; do not select controls by whether they remove significance. | Lin (2013), *Agnostic notes on regression adjustments to experimental data*, §§1–2 and results for treatment–covariate interactions and appropriate SEs in completely randomized experiments; adapt inference for other assignment designs ([paper](https://arxiv.org/pdf/1208.2301)). |
| Outlier handling | Compare defensible treatments of unusual observations under prospective rules. Preserve the original estimate and explain changes to sample and target population. | Prasad et al. (2024), same checklist, §4.5 and table 6, treatment of outliers and variable transformations ([source](https://doi.org/10.1080/19439342.2024.2318695)). |

## Observational panels

These candidates do not repair unmeasured confounding by themselves. Preserve
the panel structure and justify the inference unit.

| Candidate | Applicability and limit | Inspected methods support |
|---|---|---|
| Proxy validity | Where a proxy stands for an unmeasured confounder, audit its causal role and the identification conditions; consider a proxy-based sensitivity/test only when its assumptions and data requirements fit. Correlation with another measure cannot certify validity. Other proxy roles need their own methods support. | Miao, Geng, and Tchetgen Tchetgen (2018), *Identifying causal effects with proxy variables of an unmeasured confounder*, §§1–4: conditional independence, rank conditions, and limits with one proxy ([author manuscript](https://arxiv.org/pdf/1609.08816)). |
| Dominant-unit influence | Inspect leverage and omit-one-unit estimates at the level justified by assignment, clustering, and design. Large units need not have high leverage; singular subsamples remain reported failures or limits. | MacKinnon, Nielsen, and Webb (2023), *Leverage, influence, and the jackknife in clustered regression models*, §§2–3, cluster influence and omit-one-cluster estimates ([author manuscript](https://arxiv.org/pdf/2205.03288)). |
| Nonlinear controls | Consider a parsimonious nonlinear form for justified pre-treatment controls when a linear adjustment is inadequate; interpret the target effect consistently and avoid selecting polynomial order by significance. Preserve relevant interactions and fixed effects. | Huntington-Klein, *The Effect*, chapter 13, §13.2.2 on polynomial regression, residual shape, and overfitting ([author text](https://www.theeffectbook.net/ch-StatisticalAdjustment.html)). |

## Regression discontinuity: methods-derived

These entries come from methods literature, not empirical RDD-report coverage
in the development inventory. They concern continuity-based local-polynomial
RD; discrete-score, fuzzy, kink, or other designs need their applicable
assumptions and methods. All five entries use Cattaneo, Idrobo, and Titiunik,
*A Practical Introduction to Regression Discontinuity Designs: Foundations*
(2020; [author text](https://mdcattaneo.github.io/books/Cattaneo-Idrobo-Titiunik_2020_CUP.pdf)).

| Candidate | Applicability and limit | Inspected support in that source |
|---|---|---|
| Bandwidth sensitivity | Predeclare a defensible grid around a justified selector, preserving valid inference at each bandwidth. | §5.5, sensitivity to bandwidth choice. |
| Kernel | Compare justified local weighting choices while documenting their bandwidth and inference settings. | §4.2, local polynomial point estimation, triangular, uniform, and Epanechnikov kernels. |
| Polynomial order | Compare justified low-order local fits; avoid high-order global polynomial searches. | §4.2, discussion of local polynomial order and its consequences. |
| Donut exclusion | Where near-cutoff observations raise a substantive concern, vary the excluded neighborhood prospectively; document lost support and bandwidth reselection. | §5.4, sensitivity to observations near the cutoff. |
| Placebo cutoffs | Test artificial cutoffs away from the treatment threshold, avoiding windows contaminated by the real discontinuity. These are falsification diagnostics, not new treatment effects. | §5.3, treatment effects at placebo cutoffs. |

## Evidence boundary

Development input: replicator commit `ec32d2c`,
`replications/chain-pilot-0003/i4r-robustness-inventory.{md,json}`,
`i4r-robustness-sample.json`, and `PROTOCOL.md`. Read-only inspection of those
files informed the requested topics. Their extracted counts are approximate,
mix reproduction operations with sensitivity checks, and include
non-replication papers. They establish neither certified frequencies nor
empirical RDD-check coverage. Inventory category labels do not support any
menu item here; the named methods sources do. No heldout comparison report
was inspected and no scientific computation was run for this reference.

Sources were inspected on 2026-11-26. The Prasad et al. publisher full-text
route returned an access error; its indexed primary-source §4.5/table 6 text
was inspected. Its recommendations are candidates here, subject to the skill's
scope and person-signature rules. Record a source gap in the plan if the
selected check requires more specific support than these passages supply.
