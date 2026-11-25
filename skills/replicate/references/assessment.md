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
    "code_analyse_complet": "data/Estimations_final.do lines 186-192 produce Table 1",
    "donnees_analyse_completes": "data/Final_panel_v6.dta holds every Table 1 variable",
    "chaine_brute_incomplete": "the raw chain stops at the panel: neither CRS records nor cleaning code",
    "code_nettoyage_inaccessible": "no script builds data/Final_panel_v6.dta from CRS records"
  },
  "non_etabli": {"donnees_brutes_completes": "CRS activity records not in the deposit"},
  "a_evaluer": ["cra_reussie", "cra_echouee", "crr_reussie", "crr_echouee"],
  "level": "non_etabli",
  "history": [{"date": "2026-12-01", "verb": "assess", "level": "non_etabli"}]
}
```

In this example no rule matches before a run: L5 or L4 waits for the
outcome from the analysis data. A package that is complete on paper still
reads `non_etabli` until `reproduce` runs.

- **`criteres`** holds only the criteria that are established, each mapped to
  one verified piece of evidence (path and line, URL and passage, or CSV
  row). Its shape is the dossier of the CIRED `classer.py --preuves` option,
  so the export is mechanical:
  `{"<citekey>": {"criteres": <criteres>}}`.
- **`non_etabli`** maps each criterion that was examined but not established
  to the reason. A missing piece and a failure are both evidence.
- **`a_evaluer`** lists the criteria not yet examined: the run criteria until
  `reproduce` runs.
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
level = next((r["classe"] for r in rules if all(c in a["criteres"] for c in r["criteres"])), "non_etabli")
```

- **`history`** gets one entry per verb run that changed the level.
  `reproduce` updates this same file. It never writes a second assessment.

The run criteria refer to the main result. `cra_reussie` holds when every
statistic of the main result matches from the analysis data, and
`cra_echouee` when one does not. `crr_*` is the same check from the raw data.
The evidence is the path of the CSV and its rows' `outcome_key`.

## The six-row table, derived

Each row comes from the criteria and from `out/reproduce.csv`. The grid has
no criterion for every "Partially" cell. There, the evidence text of
`analyse_partiellement_accessible` or `chaine_brute_incomplete` must name
which piece is partial, and the row reads it. A "No" criterion
outranks that reading: `code_nettoyage_inaccessible` makes the cleaning-code
row No even when `chaine_brute_incomplete` is also established.

| Row | Fully | Partially | No |
|---|---|---|---|
| Raw data provided | `donnees_brutes_completes` | `donnees_brutes_partielles` | `donnees_brutes_inaccessibles` or `aucune_donnee_accessible` |
| Cleaning code provided | `code_nettoyage_complet` | `chaine_brute_incomplete` naming the cleaning code | `code_nettoyage_inaccessible` or `aucun_code_accessible` |
| Analysis data provided | `donnees_analyse_completes` | `analyse_partiellement_accessible` naming the data | `aucune_donnee_accessible` |
| Analysis code provided | `code_analyse_complet` | `analyse_partiellement_accessible` naming the code, or `scripts_accessibles` alone | `aucun_code_accessible` |
| Reproducible from analysis data | every `stage=reproduce` row from analysis data is `match` | some `match`, some not | none match, or the code does not run |
| Reproducible from raw data | same, for rows from raw data | same | same, or raw data or cleaning code missing |

A row whose inputs are still `a_evaluer` is printed as "not yet assessed",
never guessed. When no row from raw data exists because the package starts
at the analysis data, "Reproducible from raw data" is No, and the reason is
recorded.

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
row, matches included. The report shows only discrepancies and rounds to
three digits.

## manifest.json

The identity and provenance fields are shared with replicator's Phase B
`run.yaml`, so its pipeline can later take in a hand replication:

```json
{
  "doi": "10.1017/S1355770X26100679", "citekey": "gavard2026climate",
  "zotero_item": "<item key>", "family_id": null,
  "package": {"source_url": "https://zenodo.org/records/7149667", "version": "1",
              "retrieved": "2026-12-01", "language": "Stata"},
  "files": [{"path": "data/Final_panel_v6.dta", "sha256": "…", "bytes": 0,
             "license": "CC-BY-4.0", "redistributable": true}],
  "environment": {"interpreter": "Stata 18 MP", "lockfile": "reproduce/requirements.lock"},
  "template": {"name": "I4R Template: Reproduction Report - General", "version": "…"}
}
```

`template` is added by `report`. `fetch.sh` reads `files[]` and fails on the
first hash that differs.
