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
the comparison and auxiliary CSV contracts are in `references/assessment.md`. Before retrieving worked
examples or case answers, apply § Validation exposure and calibration. The
Gavard Scotch hand reproduction is mapped to these verbs in
`references/gavard-scotch-mapping.md`; it contains exposed development evidence.

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
fetch.sh         downloads or accepts supplied inputs into data/, checks exact-representation hashes
assessment.json  ACRe level, per-criterion evidence, grid id
data/            fetched inputs, git-ignored
reproduce/  robustness/  report/
out/             tracked comparison and separate auxiliary CSVs, full precision
```

The `probe` verb writes into `robustness/`. Teammates read the I4R word on
disk; the verb keeps the shorter action name.

**Teammates do not run this harness.** Every file in the folder must work
without it. Put plain Markdown in `README.md` and `robustness/plan.md`, and
put CSVs in `out/`. Scripts run with the paper's own software (Stata, R,
Python) from a command written in `README.md`. Never put a harness path, a
skill call or an agent instruction in the folder.

## Validation exposure and calibration

Before retrieving a worked example, prior replication report, case note, or
answer-bearing helper output, establish whether the run is ordinary
reproduction/appraisal, calibration/development, or blind validation. Record
prior exposure of executors, helpers, and any plan signers, including case
answers and evidence used to derive the rules being evaluated, in `README.md`.
Pass the purpose, exposure record, and excluded sources to helpers before
retrieval; omit conflicting discovery or existing-note steps. Unknown exposure
stays disclosed and cannot support a claim of blind validation.

For blind validation, keep answers out of execution and signing contexts until
results are frozen. Exposed or development papers remain usable for ordinary
reproduction with disclosure, but cannot independently validate rules derived
from them. This applies across all verbs, not just comparison with a held-out
report. Follow `references/validation.md` for calibration freezes, unused-table
evaluation, and fresh-paper/cohort validation. Existing assessment scope,
printed-digit tolerance, ACRe meanings, and human signing authority still apply.

## Assessment scope

Whole-paper assessment remains the default, including for Games. An explicit
caller request may add a **selected-target assessment** for named claims,
outputs, or estimates. Declare it from the original paper before inspecting
its dependencies or running code; a package's available files cannot choose
the target. Follow `references/assessment.md` § Selected-target assessment
for its declaration, separate namespace, and evidence rules. The canonical
whole-paper dossier, level, and table keep their existing meanings. A selected
result never substitutes for them or exports as a whole-paper grid criterion.

Carry the selected scope ID through the input/producer map, execution records,
reference comparison, README, and report. Preserve unresolved whole-paper
coverage even when the selected result is Fully. Changing scope requires
rechecking affected evidence before reusing categories or comparisons.

## Every verb

- **Idempotent and resumable.** Before acting, read what the folder already
  holds. Redo only what is missing or stale: a step whose inputs changed
  hash since `manifest.json` recorded them, access has become available, or
  the governing criteria or declared target have changed. Revisit stale blocked
  reasons and claims invalidated by clarified criteria, preserving valid evidence. A
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

For a blind assessment, pass `--blind` with either `--package-url URL` or an
explicitly caller-supplied local package path. Local bytes need acquisition
provenance and observed hashes under `references/assessment.md`; no package
URL is fabricated. Use only the supplied original paper and package, their
direct source metadata, and
original-paper full-text routes that do not expose replication answers.
Skip title/web discovery, I4R reports, and prior replication notes, including
searches or existing-note retrieval through `reading-note` or another helper.
Pass this boundary to helpers before using them; omit their conflicting
steps. Record the mode, supplied URL or local-byte provenance, and excluded
sources in `README.md`. An inaccessible URL or unavailable supplied local
package stays blocked; neither authorizes discovery. Local intake changes
no answer exclusions or exposure requirements.

1. **Identify the paper.** Get the full text and the Zotero item by the
   `reading-note` skill's § 1, subject to the blind assessment boundary. Choose the
   **main result** (one table or figure) from the original paper before any
   trial, and record its authoritative passage. The CIRED protocol requires
   the same choice rule across cohorts. If full text and Zotero are unavailable,
   set `main_result` to null and record a paper blocker until an authoritative
   original-paper excerpt permits the choice. A package table cannot choose
   the result. Retain independently verifiable package evidence, but keep
   whole-paper completeness and unexamined comparisons unassessed. If a selected
   assessment was requested, also declare its exact outputs/statistics and
   numerical or literal-rendering target from authoritative paper evidence;
   unavailable target evidence blocks its declaration.
2. **Find the package.** Inspect explicitly caller-supplied local bytes when
   provided. Otherwise, in ordinary mode, check the journal supplement, the
   data archive the paper cites, the authors' pages and repositories, and a
   web search. In blind mode, inspect only the supplied URL or local bytes.
   Record every
   place looked and the access outcome in `README.md`. A login, bot wall, or
   failed download proves blocked inspection, not absent contents. Name the
   next step (for example, a logged-in download into `data/`) and resume when
   access is supplied. Check that the deposit matches the published version.
3. **Write `manifest.json` and `fetch.sh`.** Follow the checksum schema in
   `references/assessment.md`: record archive-listed algorithm, digest,
   source, and representation separately from the observed SHA-256 and byte
   count of acquired bytes. For a private local package, set
   `package.source_url` to null and record acquisition/provenance evidence;
   never invent a downloadable URL. MD5-only metadata is allowed; unavailable local
   hashes and sizes stay null. Record licence and redistribution rights.
   Generate `fetch.sh` to download or verify/copy explicitly supplied local
   bytes into `data/`, following the public/local contract in that reference.
   Validate only checksums for that exact representation, and exit non-zero
   on missing acquisition, mismatch, or blocked access.
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
   For an explicit selected target, additionally map its dependencies and derive
   its separately labelled provision rows, following `references/assessment.md`.
   Bind inspected inputs to manifest paths and exact representations; existing
   fetch/checksum requirements apply unchanged. Leave selected execution rows
   unassessed until their evidence permits a category.
5. **Preliminary-assessment note.** Draft
   `report/<citekey>-preliminary-assessment.html` and publish it as in
   § Zotero notes.

## reproduce

The goal is to rerun the authors' code on the authors' data, then compare
every reported statistic.

Before choosing implicit implementation conventions by matching paper outputs,
apply the calibration freeze and disclosure in `references/validation.md`.
When the caller has authorized translation of a Stata package, consult
`references/stata-caveats.md` for version-qualified storage, expression, and
estimator evidence. An unavailable licence alone authorizes no translation;
this reference supplies no canonical CRA eligibility or scoring ruling.

1. Run `fetch.sh`. Rebuild the authors' environment and lock it: interpreter,
   packages and versions go into `manifest.json` `environment`.
2. Map each applicable published table and figure, including appendices, to
   the source lines and comparison statistics that produce it. Keep the
   whole-paper coverage map, with gaps, in `reproduce/README.md`. Carry any
   explicit selected scope ID and its required comparison outcomes separately;
   an unexamined whole-paper map stays unresolved, without expanding the
   selected execution request.
3. Run from the analysis data first (CRA), then from the raw data (CRR)
   where the package allows. A broken script is fixed in a new file. The fix
   and its reason are recorded: a coding error found here is a robustness
   result (rule 7).
4. Write `out/reproduce.csv`: one row per compared statistic, at full
   precision. A statistic matches when it lies within half a unit of the
   paper's last printed digit. Never widen the tolerance to turn a
   discrepancy into a match. Retain produced estimates without authoritative
   printed numeric comparators in `out/auxiliary.csv`, with provenance in
   `reproduce/README.md`, under `references/assessment.md` § Auxiliary estimates.
   Auxiliary rows supply no comparison status or scoring evidence.
5. Update `assessment.json`. Set `cra_reussie` or `cra_echouee`, and
   `crr_*`, from the main result's rows, with the CSV path as evidence. Then
   re-derive the level and the table: ACRe run criteria use the main result;
   the six-row table uses whole-paper coverage (`references/assessment.md`).
   Update any selected-target execution rows separately, using only its declared
   required outcomes and scope ID. Selected success alone cannot establish a
   canonical run criterion for a different `main_result`.
6. A result that cannot be produced from the package (an input is missing)
   is recorded as `missing_input`. Never transcribe it from the paper.
   An absent comparator alone is neither a missing input nor an execution
   failure. Retain actual failed attempts and missing-input reasons separately
   in the existing run/coverage records; auxiliary retention does not erase them.

- Audit each relevant join on the authors’ actual keys and inputs at their join stage, before checker normalization or correction, recording cardinality, duplicates, matched/unmatched counts and rates with denominators, as in `references/data-audit.md`.
- Compare constructed variable definitions and sample rules across text, notes/appendices, and code, tracing constructed missingness into downstream samples and recording sourced anomalies and audit coverage as in `references/data-audit.md`.

### Selected-claim confirmation

On an explicit caller request, confirm a selected claim using the existing
`selected_target` declaration and scope ID (`references/assessment.md`).
Whole-paper reproduction remains the default; this mode leaves its coverage
and canonical ACRe criteria unchanged. Follow these steps sequentially: each
freeze precedes the execution or diagnosis it governs.

1. Before executing code, commit a dated, hashed freeze of the authoritative
   paper targets, every required statistic and analysis/raw route, tolerance
   under the existing printed-digit rule, and comparison rules (including
   rounding and exact counts where applicable). Bind the scope ID to the input
   representations, code, and locked environment. Retain the earlier target
   declaration made before dependency inspection. Record any pre-result crash
   and amendment with its reason and changed hashes before retrying; a changed
   target requires the existing scope-revision procedure.
2. When the request permits translation, name the method actually executed
   and distinguish translated confirmation from rerunning the authors' code.
   Record source and port versions, known differences, inspected equivalence
   evidence, and remaining uncertainty; an unknown historical estimator version
   stays unknown. A contemporaneous port or an interpreter version alone proves
   no estimator equivalence. Lock the executed environment. Language preferences
   remain project-local; changes to model, sample, SE, pooling, tolerance, or
   robustness still require the author's ruling.
3. Preserve the first outputs, logs, comparisons, code/input/environment
   identifiers, and their hashes before diagnosis. Keep its frozen match or
   discrepancy classifications under the declared rules. Diagnose residuals
   separately; a corrected run is a separately labelled result and cannot
   rewrite the first outcome or widen its tolerance.
4. An optional checker follows the route skill's independence rules. Preserve
   its prompt, supplied information, first output, and any disagreement. State
   independence separately for inputs, bandwidth selection, point estimates,
   and variance, as well as model family. Disclose supplied production values,
   windows, or source-derived recipes and later corrections; agreement after
   supplying a recipe is an implementation cross-check with those limits.

Worked example: replicator's
`replications/carter2024-mainclaim-cra/` at commit
`eded45754c76bd3d1822703e2cd0923a9237b8a4`, especially
`prospective-freeze.json`, `first-run-freeze.json`, `REPORT.md`, and
`reproduce/review.md`. It illustrates the workflow and its checker limits;
it supplies no required dependency or universal validation result.

## probe

The goal is to run fair robustness checks, chosen by people.

Follow these steps sequentially: the inventory precedes selection, and the
signed plan precedes execution.

1. **Inventory before selecting.** Read the paper's robustness analyses,
   including appendices and supplied code. In `robustness/plan.md`, map each
   already-run check to its source and list excluded candidates with reasons
   (already run, unfair, infeasible, or outside scope). Unavailable appendix or
   code coverage stays a named gap. Every code anomaly logged by `reproduce`
   enters the candidate list, with its disposition and evidence; an anomaly
   does not by itself establish a coding error.
2. **Draft the plan** using the rules' menu (`references/rules.md`) and the
   design-specific candidates in `references/robustness-menus.md`. Propose
   additions the paper does not already run. A robustness check asserted in the
   paper without numbers or code is eligible for the plan and cannot be rejected
   as a duplicate on that ground. Propose it when it bears on the main result;
   the signer may reject it for another explicit reason. Proposal does not
   authorize execution. For each give: the original
   estimate it is compared against, what changes, why that is a fair test,
   and who on the team runs it. Mark heterogeneity analyses and extensions as
   extras (rule 5). Choose any drop-one unit from the design, assignment, and
   clustering structure; justify it rather than defaulting to observations.
   Keep case variables, thresholds, and unit choices in the paper folder.
3. **Fix reporting before execution.** Give each planned check an identifier
   and require a reported disposition: completed, failed, blocked, or withdrawn,
   with a reason and evidence. Report completed results beside the original
   estimate, including adverse or inconclusive results. A count of passes
   cannot decide an overall robustness verdict. Preserve the amendment history
   and reasons for changes, including withdrawals; amendments need renewed
   signature before execution under the changed plan.
4. **Halt.** The plan is signed when it carries a line
   `Signed-off-by: <name>, <YYYY-MM-DD>` written by a person. An agent never
   writes that line. Without it, `probe` reports the plan path and stops.
5. **After signing**, write one script per check under `robustness/`. Each
   appends rows to `out/robustness.csv` with `stage=robustness` and `spec`
   naming the alteration. A rerun runs only checks with no rows yet; inspect
   the disposition ledger first so a failure, block, or withdrawal is not
   mistaken for an unattempted check. Record every planned check's disposition
   in `robustness/plan.md`, including those that produce no CSV rows.

For validation against a held-out replication report, apply § Validation
exposure and calibration before reading it or preparing the plan. The executor
and plan signers must not have read that report; retain the answer boundary
until results are frozen.

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
   from `out/reproduce.csv` and `out/robustness.csv`. This comparison display
   rule does not suppress or round the stored auxiliary artifact. Identify
   auxiliary estimates separately with their provenance and lack of numeric
   comparator; exclude them from match/discrepancy totals and score denominators.
   Put each robustness result beside its original estimate.
   Disclose AI assistance. If selected-target work was requested, also show its
   separately labelled six-row table and target declaration. Keep any reference
   comparison scoped and distinguish printed categories from inferences under
   `references/assessment.md`; mismatched or unknown scope supplies no
   unqualified agreement score.
3. List the questions for the original authors. Do not send them.
4. Draft `report/<citekey>-reproduction-report.html` and publish it as in
   § Zotero notes.

### Causal identification review

Include a separate identification section in the report, following
`references/identification-review.md`: declare the causal claim, draw a
sourced DAG, adapt the eleven prompts to the study design, and give an argued
reviewer judgment with its unresolved assumptions. Write for a non-specialist
economist. Seek a reviewer from another model family through the route skill
for substantive causal reasoning, and disclose an unavailable perspective.

This source-based appraisal runs no new estimates. Any proposed empirical
check goes through the existing signed `probe` plan. Keep causal
identification, statistical significance, and estimator robustness distinct;
the identification judgment changes neither ACRe nor any of the six
Reproducibility Table rows, all of which assess computation. A favorable or
adverse judgment earns the same evidential scrutiny (rule 4).

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
after, the table rows that changed, the discrepancy count from comparison
rows only (excluding `out/auxiliary.csv`), and the
next blocker. Name any selected scope ID and its separately labelled changes.
For `probe`, either the plan path awaiting signature or the checks run.
