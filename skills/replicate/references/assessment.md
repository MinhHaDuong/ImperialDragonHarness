# Assessment, manifest and output schemas

Three files carry the replication's state: `assessment.json`,
`manifest.json` and `out/*.csv`. The six-row Reproducibility Table and the
ACRe level are always *derived* from them. Neither is entered by hand.

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
  until `reproduce` runs. Every grid criterion belongs to exactly one of
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

- **`history`** gets one entry per verb run that changed the level.
  `reproduce` updates this same file. It never writes a second assessment.

## Package coverage and main-result runs

The four completeness criteria cover the **whole paper**, including
applicable appendix and supplementary tables, figures, and published
robustness outputs. The preselected `main_result` limits the ACRe run
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

In preliminary notes and reports, show all six derived rows, including
Fully and not yet assessed, with the evidence basis and unresolved coverage
visible. Use the literal status "not yet assessed" for an unassessed row;
if a fixed template offers only Fully/Partially/No columns, leave those
columns unmarked for that row and state the unassessed status and reason
beside it. The instruction to show only discrepancies applies to the
detailed statistic comparisons, not to this six-row status table.

## out/*.csv

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

`template` is added by `report` (chosen from `references/templates/INDEX.md`;
an adapted structure adds `"adapted": true`). Each file's `representation`
identifies the bytes requested (original format or archive-ingested `.tab`).
`archive_checksum` is nullable; when present it records the listed algorithm
(`md5` or `sha256`), digest, exact source URL, and representation it describes.
Top-level `sha256` and `bytes` are observed from the local downloaded file,
not copied or inferred from archive metadata; keep them null until inspected
bytes exist. MD5 metadata alone proves no local download or integrity check.
Record transformations as separate representations, preserving source metadata.

Generated `fetch.sh` reads `files[]`, requests the recorded representation,
and checks its applicable archive checksum and any previously observed local
SHA-256 before accepting the file. A mismatch exits non-zero. A listed `.tab`
MD5 never validates the original `.dta` (or another original format): retrieve
the matching representation, obtain its own authoritative checksum, or record
that the archive check is unavailable for the original. Compute its local
SHA-256 and size when bytes are available, without claiming archive validation.
Blocked access exits non-zero with the access step needed; a login page is
never accepted as data. A successful metadata lookup alone leaves local
verification pending. Resume after access and refresh the affected blockers
and criteria as well as the local digest; valid unchanged evidence stays put.
