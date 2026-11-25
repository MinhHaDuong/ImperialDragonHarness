---
metadata:
  category: research
name: replicate
description: "Replicate an empirical paper, I4R style: assess its package, rerun it, plan robustness checks, report."
disable-model-invocation: false
user-invocable: true
argument-hint: "<assess|reproduce|probe|report> <replication folder> [paper: DOI | citekey | Zotero item]"
---

# Replicate

`/replicate <verb> <folder> [paper]` works one paper's replication in one
folder. It follows the Institute for Replication (I4R) report format and
grades the paper on the ACRe scale. There are four verbs, each a stopping
point on one ladder:

| Verb | Runs unattended | Reads | Writes |
|---|---|---|---|
| `assess` | yes, batchable | the paper, the package | `manifest.json`, `fetch.sh`, `assessment.json`, `README.md`, preliminary-assessment note |
| `reproduce` | yes | the above, `data/` | `reproduce/`, `out/*.csv`, run criteria in `assessment.json` |
| `probe` | no: halts at `robustness/plan.md` until a person signs it | the above | `robustness/`, `out/*.csv` |
| `report` | no | everything | `report/`, reproduction-report note |

Autonomy belongs to the verb, not to a mode. Run unattended, `assess` and
`reproduce` stop at an unsigned `probe` plan. Choosing robustness checks
without a person is the cherry-picking that rule 4 forbids.

The binding rules, written for teammates who are not economists, are in
`references/rules.md`. Read it before `probe` or `report`. The assessment file and
the CSV schema are in `references/assessment.md`. The Gavard Scotch hand
reproduction, mapped step by step to these verbs, is in
`references/gavard-scotch-mapping.md`: use it as the worked example.

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory. A pre-set `IDH_ROOT` wins.

## The folder

**The caller names the folder.** It comes as an argument, or from the
session's assigned project when that project states where it hosts
replications. The skill fixes only what goes *inside* one folder. It has no
default location. Examples of hosts: replicator keeps its own replications in
`replications/<citekey>/`; a paper folder may hold `replication/`; the CIRED
reproducible-science project may host one per graded publication.

Before writing, resolve the folder and refuse two cases:

```bash
F=$(realpath -m "$FOLDER"); H=$(realpath "$IDH_ROOT")
case "$F/" in "$H"/*) echo "refused: folder inside the harness"; exit 1;; esac
git -C "$(dirname "$F")" rev-parse --show-toplevel   # must be the assigned project
```

A folder in a project other than the assigned one is reached only through
that project's tickets (`rules/guards.md`). Inner layout, as
ruled with replicator. `<citekey>` is the Zotero Better BibTeX key, ASCII
lowercase:

```
README.md        paper, method, status per check, effort and cost, next blocker
manifest.json    identity and provenance (fields in references/assessment.md)
fetch.sh         re-fetches non-redistributable inputs into data/, fails on hash mismatch
assessment.json  ACRe level, per-criterion evidence, grid id
data/            fetched inputs, git-ignored
reproduce/  robustness/  report/
out/             tracked CSVs, full precision
```

The `probe` verb writes into `robustness/`. Teammates read the I4R word on
disk; the verb keeps the shorter action name.

**Teammates do not run this harness.** Every file in the folder must work
without it. Put plain Markdown in `README.md` and `robustness/plan.md`, and
put CSVs in `out/`. Scripts run with the paper's own software (Stata, R,
Python) from a command written in `README.md`. Never put a harness path, a
skill call or an agent instruction in the folder.

## Every verb

- **Idempotent and resumable.** Before acting, read what the folder already
  holds. Redo only what is missing or stale: a step whose inputs changed
  hash since `manifest.json` recorded them. A rerun on a complete folder
  changes nothing and says so.
- **Evidence or nothing.** Every claim in `assessment.json`, `README.md` and
  the report points to a file, a line, a URL or a CSV row. A criterion
  without verified evidence stays unestablished.
- **Author files are read-only.** Copy the package into `data/` or keep it
  under its own name. Verify its hashes and never edit it. Fixes live in new
  scripts.
- **`README.md` is updated last** in every verb: status per check, hours
  spent and money spent (compute, data fees), and the next blocker.
- **Outward acts wait.** Writing to authors, sending a report to I4R and
  publishing are the author's calls.

## assess

The goal is to grade the package from its contents, before running anything.
That is ACRe levels L1 to L7. Batchable: for a reading list, or for a team
choosing among candidate papers, loop over the papers sequentially in one session, one
folder each.

1. **Identify the paper.** Get the full text and the Zotero item by the
   `reading-note` skill's § 1. Choose the **main result** (one table or
   figure) before any trial, and record it. The CIRED protocol requires
   the same choice rule across cohorts.
2. **Find the package.** Check the journal supplement, the data archive the
   paper cites, the authors' pages and repositories, and a web search. Record
   every place looked, found or not, in `README.md`; a missing package is
   evidence too. Check versions: the deposit must match the published version.
3. **Write `manifest.json` and `fetch.sh`.** Record per-file SHA-256, bytes,
   licence and whether the file may be redistributed. `fetch.sh` downloads
   into `data/` and exits non-zero on any hash mismatch.
4. **Grade.** For each grid criterion, record evidence or leave it out, in
   `assessment.json` (`references/assessment.md`). Run criteria (`cra_*`,
   `crr_*`) stay `a_evaluer`. Derive the level and the six-row
   Reproducibility Table from that evidence. Never fill the table separately.
5. **Preliminary-assessment note.** Draft
   `report/<citekey>-preliminary-assessment.html` and publish it as in
   § Zotero notes.

## reproduce

The goal is to rerun the authors' code on the authors' data, then compare
every reported statistic.

1. Run `fetch.sh`. Rebuild the authors' environment and lock it: interpreter,
   packages and versions go into `manifest.json` `environment`.
2. Map each published table and figure to the source lines that produce it.
   Keep the map in `reproduce/README.md`.
3. Run from the analysis data first (CRA), then from the raw data (CRR)
   where the package allows. A broken script is fixed in a new file. The fix
   and its reason are recorded: a coding error found here is a robustness
   result (rule 7).
4. Write `out/reproduce.csv`: one row per compared statistic, at full
   precision. A statistic matches when it lies within half a unit of the
   paper's last printed digit. Never widen the tolerance to turn a
   discrepancy into a match.
5. Update `assessment.json`. Set `cra_reussie` or `cra_echouee`, and
   `crr_*`, from the main result's rows, with the CSV path as evidence. Then
   re-derive the level and the table.
6. A result that cannot be produced from the package (an input is missing)
   is recorded as `missing_input`. Never transcribe it from the paper.

## probe

The goal is to run fair robustness checks, chosen by people.

1. **Draft `robustness/plan.md`** from the rules' robustness menu
   (`references/rules.md`). For each proposed check give: the original
   estimate it is compared against, what changes, why that is a fair test,
   and who on the team runs it. Mark heterogeneity analyses and extensions as
   extras (rule 5).
2. **Halt.** The plan is signed when it carries a line
   `Signed-off-by: <name>, <YYYY-MM-DD>` written by a person. An agent never
   writes that line. Without it, `probe` reports the plan path and stops.
3. **After signing**, write one script per check under `robustness/`. Each
   appends rows to `out/robustness.csv` with `stage=robustness` and `spec`
   naming the alteration. A rerun runs only checks with no rows yet. A
   change to a signed plan needs a new signature.

## report

The goal is the I4R report, written as a team.

1. Fetch the I4R template ("I4R Template: Reproduction Report - General",
   Zenodo) into `report/` if absent. Record its version in `manifest.json`.
   The template governs the format. Where it is silent, follow
   `references/rules.md`.
2. Write the report in `report/`. Name the paper's method in the summary
   (rule 8). Include the Reproducibility Table, derived from
   `assessment.json`, showing only discrepancies. Round values to three
   digits from `out/*.csv`. Put each robustness result beside its original
   estimate. Disclose AI assistance.
3. List the questions for the original authors. Do not send them.
4. Draft `report/<citekey>-reproduction-report.html` and publish it as in
   § Zotero notes.

## Zotero notes

The CIRED protocol keeps three child notes under the paper's Zotero item:

- the reading note, written by the `reading-note` skill (which also records
  the replication-package fields);
- the preliminary assessment, from `assess`;
- the reproduction report, from `report`.

Draft each note as HTML with YAML frontmatter carrying `zotero_item` (the
format of `skills/reading-note/references/template.md`). Name the file per
paper and note type, as above. After the draft is reviewed and merged by the
host project's route, publish it:

```bash
python3 "$IDH_ROOT/scripts/zotero.py" publish-notes --project <host project> \
  --collection "<collection>" --dry-run <draft>.html   # then without --dry-run
```

Publishing is blocked? Report it pending, and keep the draft.

## Output to the user

Print one line per verb run: the folder, the verb, the ACRe level before and
after, the table rows that changed, the discrepancy count in `out/`, and the
next blocker. For `probe`, either the plan path awaiting signature or the
checks run.
