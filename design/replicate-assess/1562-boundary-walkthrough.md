# Raw and cleaning boundary walkthrough

Ticket: `tickets/1562-replicate-assess-raw-analysis-and-cleani.erg`

These are acceptance scenario walkthroughs of the facts supplied in ticket
1562, not independent empirical validation of the named packages or I4R
reports. The external replicator validation branch, packages under
`~/CNRS`, and CIRED grid are unavailable in this checkout. No numerical
reproduction or grid-level computation was attempted. The existing grid
vocabulary and the whole-paper inventory/main-result distinction remain.

## Initial reading

Before the change, `assessment.md` let `code_nettoyage_inaccessible`
override partial coverage without checking its scope. This yielded No for
the supplied Blair and Arechar cleaning examples. It did not define the
starting-extract boundary or separate provided code from absent inputs and
execution defects. The acceptance check is whether the revised guidance
settles these concrete classifications without inferring package facts.

## Walkthrough after the change

| Supplied scenario | Reading under the revised reference | Evidence and limit |
|---|---|---|
| Blair: `replication.do` lines 42–260 build lags, imputations, and sample dummies from a deposited panel; the panel-build script is absent. | Cleaning code Partially via `chaine_brute_incomplete` naming available operations and the missing build stage. | The available transformations contradict total cleaning-code absence; they do not prove raw provision or complete cleaning coverage. |
| Arechar: one dataset cannot clearly be classified as raw or analysis; code mixes cleaning and analysis. | Raw data Partially via `donnees_brutes_partielles`; cleaning Partially via `chaine_brute_incomplete` with the observed operations and unresolved coverage. From-raw table row Partially for the examined boundary ambiguity, with that reason. | Preserve the supplied uncertainty. No `donnees_brutes_completes`, total-absence criterion, or `crr_reussie` follows. Unexamined output comparisons must still be disclosed; ambiguity does not certify execution. |
| Carter and Moscona: authors deposit the starting extracts needed by their documented cleaning pipelines; entire upstream archival/GIS or FOIA/patent/weather databases are absent. | Raw data Fully if those extracts cover every applicable whole-paper path. | Upstream database absence alone is no gap. Verify extract coverage; clearly final panels cannot acquire raw status by being deposited. The ticket supplies no package-wide inventory proving Fully independently. |
| Graham: complete cleaning scripts exist, but a required dictionary XLSX is missing. | Cleaning code Fully when every documented path's code is present; missing dictionary recorded against inputs and execution. | `code_nettoyage_complet` does not claim that inputs are complete or that a run succeeds. Inspect coverage rather than infer missing code from the missing dictionary. |
| Carter: a provided script writes no output. | Code completeness remains a code-inspection question; record the failed execution separately. | No output alone does not establish an omitted cleaning stage. If diagnosis instead shows missing code, update the code criterion with that evidence. |
| True-absence positive control: a complete inventory and inspection verify final analysis data only and no cleaning transformations or accessible cleaning code on any applicable path. | Cleaning code No via `code_nettoyage_inaccessible`; raw provision No when verified absent; from-raw reproduction No when no raw run is possible. | This supplied control establishes total absence. It contrasts with available cleaning operations plus a missing build stage, which are Partially. |
| Contradictory dossier: `code_nettoyage_inaccessible` coexists with evidence of available cleaning transformations. | Resolve the evidence and correct the total-absence criterion before deriving the row. | An unavailable build stage does not erase present transformations. If partial-chain evidence instead names only available raw inputs, total cleaning absence can consistently remain No. |

The walkthrough passes the ticket's three exit criteria: operational raw and
cleaning definitions, an explicit examined-ambiguity reading, and replacement
of blanket No precedence with component-specific evidence reconciliation.
Template selection and the six-row table's coverage stay as introduced by
1559 and 1561. Ticket 1563's blocked/blind, MD5, and generated-data handling
remain outside this change.
