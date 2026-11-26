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

Before writing, resolve the folder. Refuse it inside the harness or
outside any project; otherwise check it is the assigned project:

```bash
F=$(realpath -m "$FOLDER")
C=$(git -C "${IDH_ROOT:?}" rev-parse --path-format=absolute --git-common-dir) ||
  { echo "refused: harness root unresolved"; exit 1; }
H=$(dirname "$C")   # the primary checkout; harness worktrees sit inside it
[ -f "$H/rules/guards.md" ] || { echo "refused: IDH_ROOT is not the harness"; exit 1; }
case "$F/" in "$H"/*) echo "refused: folder inside the harness"; exit 1;; esac
D=$F; while [ ! -d "$D" ]; do D=$(dirname "$D"); done   # nearest existing parent
git -C "$D" rev-parse --show-toplevel || { echo "refused: not in any project"; exit 1; }
```

A folder in a project other than the assigned one is reached only through
that project's tickets (`rules/guards.md`). Inner layout, as
ruled with replicator. `<citekey>` is the Zotero Better BibTeX key, ASCII
lowercase:

```
README.md        paper, method, status per check, effort and cost, next blocker
manifest.json    identity and provenance (fields in references/assessment.md)
fetch.sh         re-fetches inputs into data/, checks hashes for the selected representation
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
  hash since `manifest.json` recorded them, access has become available, or
  the governing criteria have changed. Revisit stale blocked reasons and
  claims invalidated by clarified criteria, preserving valid evidence. A
  rerun on a complete, still-valid folder changes nothing and says so.
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
Contents alone settle L1 to L3, L6 and L7; L4, L5
and L8 to L10 wait for `reproduce`. Batchable: for a reading list, or for a team
choosing among candidate papers, loop over the papers sequentially in one session, one
folder each.

For a blind assessment, pass `--blind --package-url URL`. Use only the
supplied original paper and package, their direct source metadata, and
original-paper full-text routes that do not expose replication answers.
Skip title/web discovery, I4R reports, and prior replication notes, including
searches or existing-note retrieval through `reading-note` or another helper.
Pass this boundary to helpers before using them; omit their conflicting
steps. Record the mode, supplied URL, and excluded sources in `README.md`.
An inaccessible supplied URL stays blocked; it does not authorize discovery.

1. **Identify the paper.** Get the full text and the Zotero item by the
   `reading-note` skill's § 1, subject to the blind assessment boundary. Choose the
   **main result** (one table or figure) from the original paper before any
   trial, and record its authoritative passage. The CIRED protocol requires
   the same choice rule across cohorts. If full text and Zotero are unavailable,
   set `main_result` to null and record a paper blocker until an authoritative
   original-paper excerpt permits the choice. A package table cannot choose
   the result. Retain independently verifiable package evidence, but keep
   whole-paper completeness and unexamined comparisons unassessed.
2. **Find the package.** In ordinary mode, check the journal supplement, the
   data archive the paper cites, the authors' pages and repositories, and a
   web search. In blind mode, inspect the supplied URL directly. Record every
   place looked and the access outcome in `README.md`. A login, bot wall, or
   failed download proves blocked inspection, not absent contents. Name the
   next step (for example, a logged-in download into `data/`) and resume when
   access is supplied. Check that the deposit matches the published version.
3. **Write `manifest.json` and `fetch.sh`.** Follow the checksum schema in
   `references/assessment.md`: record archive-listed algorithm, digest,
   source, and representation separately from the observed SHA-256 and byte
   count of downloaded bytes. MD5-only metadata is allowed; unavailable local
   hashes and sizes stay null. Record licence and redistribution rights.
   Generate `fetch.sh` to download into `data/`, validate only checksums for
   that exact representation, and exit non-zero on mismatch or blocked access.
   It must not compare an ingested `.tab` checksum with an original file or
   treat listed metadata alone as verified downloaded bytes. Record the local
   SHA-256 when bytes become available, preserving the archive checksum.
4. **Grade.** Account for every grid criterion exactly once as established,
   examined but not established, or unexamined, with blocked reasons where
   applicable (`references/assessment.md`). An empty `criteres` is valid only
   with that full dossier. Inventory the whole paper, including applicable
   appendix outputs, for package completeness; an unseen paper blocks this
   coverage. Assess generated analysis inputs only under the inspected
   producer-chain conditions in that reference. Run criteria (`cra_*`,
   `crr_*`) stay `a_evaluer` until execution. Derive the level and six-row
   Reproducibility Table from the evidence; blocked unknowns remain unassessed.
5. **Preliminary-assessment note.** Draft
   `report/<citekey>-preliminary-assessment.html` and publish it as in
   § Zotero notes.

## reproduce

The goal is to rerun the authors' code on the authors' data, then compare
every reported statistic.

1. Run `fetch.sh`. Rebuild the authors' environment and lock it: interpreter,
   packages and versions go into `manifest.json` `environment`.
2. Map each applicable published table and figure, including appendices, to
   the source lines and comparison statistics that produce it. Keep the
   whole-paper coverage map, with gaps, in `reproduce/README.md`.
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
   re-derive the level and the table: ACRe run criteria use the main result;
   the six-row table uses whole-paper coverage (`references/assessment.md`).
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

1. Choose the I4R template from `references/templates/INDEX.md`, using the
   context the folder already holds: the template I4R named in the assignment
   first. Otherwise use the kind of work and the paper's field and journal:
   choose Commentary from Forensic Report for forensic commentary on specific
   problems; choose Psychological Science Phase 2 for a reproduction report
   in that I4R project; use General for other reproduction and robustness
   reports. Psychology alone does not establish Phase 2 membership. If the
   context leaves the specific templates equally applicable, use General and
   explain the uncertainty. Copy the chosen Word or
   LaTeX files into `report/` if absent and record in `manifest.json`
   `template{name, record, version, reason}`; the reason is one sentence naming
   the evidence. The template governs the format. Where it is silent, follow
   `references/rules.md`.
   No template fits (a format or field none covers)? Say so, give the reason,
   and propose an adapted structure for this replication in
   `report/structure.md`, starting from the closest template and naming each
   section changed. Record the closest template with `"adapted": true`. Never
   add a new generic template to the skill. A person confirms the adapted
   structure before the report is written.
   Optionally read each record's `links.latest` on Zenodo (needs the network)
   and report a newer version; do not switch to it.
2. Write the report in `report/`. Name the paper's method in the summary
   (rule 8). Include all six rows of the Reproducibility Table, derived from
   `assessment.json`, with each evidence basis and any "not yet assessed"
   status visible (`references/assessment.md`). Distinguish provision-based
   impossibility from observed execution failure. Show only discrepancies
   in the detailed statistic comparisons, rounding values to three digits
   from `out/*.csv`. Put each robustness result beside its original estimate.
   Disclose AI assistance.
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
