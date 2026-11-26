# Ticket 1561: package coverage walkthrough

These are documentation acceptance scenarios, using the facts supplied in
ticket 1561 and a synthetic positive control. The external replicator
validation report, packages, and CIRED grid are unavailable in this checkout;
no package inspection, numerical reproduction, or ACRe level validation is
claimed. Read against `skills/replicate/references/assessment.md` and the
worked Gavard mapping.

| Scenario and supplied evidence | Criterion decision | Derived provision cell |
|---|---|---|
| Arechar: main-result code present; Stata code absent for Figures 2–5; Figure 6 R code reads absent deposited inputs | Withhold `code_analyse_complet` and `donnees_analyse_completes`; `analyse_partiellement_accessible` names the missing code and data separately | Analysis code: Partially; analysis data: Partially |
| Moscona: main-result code present; appendix Tables A18 and A20 code absent | Withhold `code_analyse_complet`; `analyse_partiellement_accessible` names the missing appendix code. The absolute Dropbox path alone establishes no additional completeness claim | Analysis code: Partially |
| Synthetic complete package: output inventory covers every applicable main-text and appendix output, with every analysis file, raw input, cleaning path, and analysis script verified | Establish all four completeness criteria from that inventory | All four provision rows: Fully |
| Synthetic main-only inspection: Table 1 inputs verified; remaining paper and appendices unexamined | Leave whole-paper completeness `a_evaluer`; a Table 1 path cannot establish it | Unexamined provision rows: not yet assessed |

The complete-package control establishes provision only. Before a run, its
execution rows remain not yet assessed. For the same inventory after all
required analysis and raw comparisons match, both execution rows become
Fully, while `cra_reussie` and `crr_reussie` follow the chosen main result.

If the main result matches but a known appendix input is missing, record
that appendix comparison as `missing_input`: the applicable whole-paper
execution row becomes Partially. The main-result ACRe success criterion can
still hold. If only the main result ran and appendix comparisons remain
unexamined, the execution row stays not yet assessed, even with an all-match
CSV subset. These checks prevent a vacuous Fully from incomplete coverage.

The Gavard example now records A2–A3 missing sector inputs as partial
analysis-data coverage and `missing_input`, rather than promoting Table 1
inputs to whole-paper completeness. Existing discrepancies also prevent a
Fully execution cell. No assertion about missing analysis code follows from
missing sector data alone.
