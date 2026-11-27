# Worked example: the Gavard Scotch reproduction, mapped to the verbs

Gavard and Schoch (2026), "International climate finance and emission
reductions", *Environment and Development Economics*, was reproduced by hand
with agent help in September 2026. The reproduction ported the Stata
package to Python. Its record is in the author's paper folder (`audit/`
`reproduction-final-2026-09-22.md`, `final-replication-package-search-2026-09-15.md`,
`reproduction/python/`). Each step it took has a home in a verb below, or a
recorded reason to stay outside the skill.

## Exposure and historical status

This is an answer-bearing, exposed worked example. Its estimator choices used
published results for calibration; reading it creates prior exposure for a
Gavard validation run. Use it for ordinary reproduction or development with
disclosure under `validation.md`, not as independent validation of rules
derived from this case. The September findings below remain a dated account,
not a current adjudication of estimator equivalence or canonical CRA status.
The routing describes where to retain evidence; it grants no additional
translation or robustness-execution authority.

The later Replicator transcription separates calibration on Tables 1 and B3
from evaluation on other tables after those choices were fixed. That is a
same-paper unused-table check, not fresh-paper validation. Its source is
`replications/gavard2026climate/reproduce/README.md` at Replicator commit
`03af9ef6ff3b64230addbae96e8be3403e1cf971`; `COMPARE-PORT.md` there records later
comparisons with the September port. These later records do not overwrite the
historical findings in this mapping.

## September 2026 record

| Step taken in September 2026 | Verb | Where it lands |
|---|---|---|
| Search for a package matching the published version: Zenodo record and versions API, the journal page, authors' sites and GitHub, a web search; a mismatch found (the script normalises by lagged emissions, the paper by mean GDP) | `assess` | step 2; the places searched, in `README.md`; the version mismatch as evidence in `non_etabli` |
| Check the ZIP's CRC and SHA-256, compare each extracted file byte for byte, keep author files read-only | `assess` | `manifest.json` `files[]`, `fetch.sh` |
| Record that the package starts at the aggregate panel (no transaction-level CRS records, no construction code) | `assess` | `donnees_brutes_*` and `code_nettoyage_*` evidence; "Reproducible from raw data": No, with reason |
| Separate environment from a lockfile; tests on the port | `reproduce` | step 1, `manifest.json` `environment` |
| Map each applicable published table and figure, including appendices, to its code and comparison statistics | `reproduce` | step 2, `reproduce/README.md` |
| Port the GEE estimator and fix a residual-moment denominator that failed the published coefficients | `reproduce` | step 3; the re-coding in other software is also a robustness check (rule 7) |
| Compare Tables 1-3, B1-B6 and A1 at half a unit of the last printed digit; keep the six strict exceptions explicit | `reproduce` | step 4, `out/reproduce.csv` `status=discrepancy` |
| Mitigation bound printed 0.491%, reproduced 0.498953% | `reproduce`, then `report` | one discrepancy row; listed in the report |
| Sector tables A2-A3 not producible (no sector inputs) | `assess`, then `reproduce` | partial whole-paper analysis-data coverage, never `donnees_analyse_completes`; step 6 records `status=missing_input`. If other outputs match, the whole-paper analysis execution row is Partially; main-result `cra_*` is assessed separately |
| Rerun the authors' own extra robustness models (TWFE, GMM from FurtherRobustness.do); three rank failures not estimated | `reproduce` | the authors' published checks are reproduction targets, with `spec=original` |
| Conditional annual-rate CPI correction as a sensitivity | `probe` | one check in `robustness/plan.md`, compared with the reproduced original |
| Adaptation-minus-mitigation contrast, p = 0.202 | `probe` | a check on the main model, if the team signs it |
| Questions for the authors (CRS extraction, CPI series, full-precision Stata output, GMM logs, A2-A3 inputs) | `report` | step 3: listed, not sent |
| Request to the authors for the final package, sent 15 September on the author's instruction | none | outward act: the author's call, outside every verb |
| Causal interpretation: allocation, good and bad controls, alternative DAGs, scale against orientation | none | a scholarly comment, not robustness. It is an extension (rule 5), allowed in the report as an extra at most |
| Revising the comment manuscript from the audit | none | manuscript prose belongs to the paper project, not to the replication |

What the example teaches. First, `assess` alone found the decisive facts:
the package did not match the published version and stopped at aggregate
data. Second, the step that took longest, porting the estimator, sits
inside `reproduce` as a record of the translated work, subject to the current
translation and scoring boundaries. Third, the September work ran no signed robustness plan:
the CPI sensitivity was chosen by the analyst. The skill would require a
signature before running it.
