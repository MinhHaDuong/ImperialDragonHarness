# Ticket 1571 documentation evidence

Base: `6bf8c1acfc78ae7bbab664926fc7575919923ab8` (accepted integration
branch). Documentation change: `ea9c5320ff735e41fe8731bfe1dbc532f4428040`.
No scientific execution. No heldout report read. No source-project write.
Parent 1570 retains its post-pilot sign-off decision.

## Source-to-item audit

Every menu row uses a named methods source. No row relies on inventory
category counts or claims two uninspected report examples.

| Menu item | Inspected source passage and support | Boundary checked |
|---|---|---|
| Meta publication bias | Page, Higgins, and Sterne, Cochrane chapter 13, “Selection models”: vary selection assumptions and compare adjusted effects. | Asymmetry has competing explanations; adjustment is assumption-dependent. |
| Meta REML/DL | Deeks et al., Cochrane chapter 10, §10.10.4: both heterogeneity estimators and performance. | Preserve effect data; no p-value selection. |
| Meta drop-one | Viechtbauer/Cheung 2010, §4: case deletion; discussion rejects routine deletion of extreme studies. | Independent-study unit; dependent effects acknowledged. |
| DiD threshold/dose | Altman/Royston 2006 on costs of dichotomization; Callaway/Goodman-Bacon/Sant'Anna continuous-treatment draft, introduction/§3 on dose effects and selection. | Conceptual sensitivity question inferred from these methods, not a prescribed threshold grid. Estimand changes and subgroup extras explicit. |
| DiD event study | Callaway/Goodman-Bacon/Sant'Anna 2024, sections I–II on event-time/dose aggregation. | Timing/intensity fit; dynamics do not prove identification. |
| DiD multiple testing | Romano/Wolf 2007, simultaneous hypotheses, familywise/generalized error criteria, stepdown procedures. | Family and dependence conditions must be chosen prospectively. |
| Experiment PAP | Prasad et al. 2024, §4.5/table 6 indexed primary text: PAP concordance. | Disclosure, not automatic wrongdoing or model-signing authority. |
| Experiment controls | Lin 2013, §§1–2: unadjusted/adjusted/interacted estimators, pretreatment covariates, assignment and SE conditions. | Main results concern completely randomized experiments; other designs need adapted inference. |
| Experiment outliers | Prasad et al. 2024, §4.5/table 6 indexed primary text: treatment of outliers and transformations. | Prospective defensible rules, sample/estimand consequences. |
| Panel proxy | Miao/Geng/Tchetgen Tchetgen 2018 manuscript, §§1–4: confounder proxies, conditional independences, rank conditions, one-proxy limits. | Limited to this proxy role; other roles require their own support. |
| Panel dominant units | MacKinnon/Nielsen/Webb 2023 manuscript, §§2–3: cluster influence, omit-one-cluster estimates, singular subsamples. | Design/assignment/clustering unit justified; size differs from leverage. |
| Panel nonlinear controls | Huntington-Klein, The Effect §13.2.2: polynomial shape, residuals, overfitting, against significance-based order selection. | Parsimonious pre-treatment controls; does not repair confounding. |
| RD bandwidth | Cattaneo/Idrobo/Titiunik Foundations §5.5: bandwidth sensitivity. | Methods-derived; prospective grid with appropriate inference. |
| RD kernel | Same, §4.2: kernel weights and selector dependence on kernel. | Bandwidth/inference settings recorded. |
| RD polynomial | Same, §4.2: local order consequences and limits. | Low-order local fit; no global high-order search. |
| RD donut | Same, §5.4: near-cutoff exclusions and reselection. | Lost support, justified excluded neighborhood. |
| RD placebo cutoffs | Same, §5.3: artificial cutoffs without true treatment change. | Avoid windows crossing true threshold; diagnostic interpretation. |

The reference carries direct source links and locators. Public source
inspection used primary publications, author manuscripts, and the Cochrane
methods handbook. Publisher access for Prasad and Altman/Royston returned
403 on full-text opening; indexed publisher text was inspected. Prasad's
indexed §4.5 supports PAP/outliers; its general covariate-balance statement
was insufficient for an alternative-control recommendation, so that row
uses the inspected Lin paper. No unresolved source gap is hidden.

Pinned development inputs inspected read-only at replicator `ec32d2c`:
`PROTOCOL.md`, inventory Markdown and JSON, and sample JSON under
`replications/chain-pilot-0003/`. Inventory frequencies remain approximate,
include non-replication papers, and mix computational reproduction with
sensitivity work. They provide no empirical RDD-check coverage for this menu.
The pilot's model signatures remain a deviation, not a generic permission.

## Semantic preservation

A direct Python byte comparison against the base passed for SKILL.md before
`## probe`, after `## report`, the person-written signature paragraph, and
all of `references/rules.md`. This preserves four verbs, ACRe/table meaning,
selected-claim confirmation (1568), identification review (1569), and rule 4.
The sole changed skill section is probe; its new reference supplies candidates.

Manual exit-criterion audit: inventory includes appendix/code gaps and
exclusions; every reproduce anomaly becomes a candidate, with dispositions;
reporting is prospective and covers every planned check, including failures,
blocks, and withdrawals; amendments retain history and require renewed
signature; pass counts cannot determine the verdict. Scope classification,
comparison with the original, design-specific deletion units, and validation
exposure limits are explicit. Ordinary report appraisal remains unchanged.

## Verification

On the committed/rebased documentation change, `make lint` passed 191 tests
and `make check-fast` passed 1966 tests (seven existing deprecation warnings).
`git diff --check` passed. No prose wording tests were added. The first
sandboxed lint attempt could not write the uv cache; the authorized escalation
ran the locked environment successfully. Semantic review and gaze records are
reported separately on their exact reviewed heads.
