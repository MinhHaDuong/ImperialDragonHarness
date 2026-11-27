---
metadata:
  category: research
name: replicate
description: "Replicate a paper through inventory, identification, rerun, approved challenges, and a cumulative I4R report."
disable-model-invocation: false
user-invocable: true
argument-hint: "<inventory|identify|rerun|challenge|complete> <replication folder> [paper: DOI | citekey | Zotero item]"
---

# Replicate

`/replicate <stage> <folder> [paper]` works one paper's replication in one
folder. Requesting stage k performs stages 1..k in this order, reusing valid
computations while rereading every written section. Only these five command
names are accepted; historical names are not aliases.

| # | Stage | Adds to the local report | Execution and stop |
|---|---|---|---|
| 1 | `inventory` | Opening, original claim, package and four provision rows | No estimates; unattended, batchable |
| 2 | `identify` | Identification immediately after the opening | No estimates; unattended targeted source appraisal |
| 3 | `rerun` | Computational Reproducibility and two execution rows | Scope choice before computation unless supplied by caller |
| 4 | `challenge` | Robustness Reproduction | Only checks approved under `references/probe-approval.md`; no signature timeout |
| 5 | `complete` | Conclusion, rewritten introduction, AI Disclosure | No new estimates; outward acts remain the author's |

Every stage compiles the report through its latest section and updates one
local Zotero-note draft. A blocked stage compiles available evidence and states
what has not run; it cannot claim completion or bypass its prerequisite.
Follow § Every stage and `references/cumulative-report.md` throughout.
Apply `references/report-style.md` for report presentation and disclosure.
Qualify discrepancies under `references/discrepancies.md`, retaining strict outcomes.
Track acquisition producers and replay evidence under `references/acquisition.md`.

The binding rules, written for teammates who are not economists, are in
`references/rules.md`. Read them before starting the chain. The assessment and
comparison/auxiliary/assertion CSV contracts are in `references/assessment.md`.
Before retrieving worked examples or case answers, apply § Validation exposure
and calibration. `references/gavard-scotch-mapping.md` routes historical
exposed development evidence to the current stages without changing its records.

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
out/             tracked comparison, auxiliary, and assertion CSVs, full precision
```

The `challenge` stage writes into `robustness/`. Storage paths and literal
CSV stage labels remain contractual: `reproduce/`, `out/reproduce.csv`,
`stage=reproduce`, and `stage=robustness` retain their names. These are data
contracts, not additional commands.

**Teammates do not run this harness.** Every file in the folder must work
without it. Put plain Markdown in `README.md` and `robustness/plan.md`, and
put CSVs in `out/`. Scripts run with the paper's own software (Stata, R,
Python) from a command written in `README.md`. Never put a harness path, a
skill call or an agent instruction in the folder.

## Validation exposure and calibration

Before retrieving a worked example, prior replication report, case note, or
answer-bearing helper output, establish whether the run is ordinary
reproduction/appraisal, calibration/development, or blind validation. Record
prior exposure of executors, helpers, and any plan approvers, including case
answers and evidence used to derive the rules being evaluated, in `README.md`.
Pass the purpose, exposure record, and excluded sources to helpers before
retrieval; omit conflicting discovery or existing-note steps. Unknown exposure
stays disclosed and cannot support a claim of blind validation.

For blind validation, keep answers out of execution and approval contexts until
results are frozen. Exposed or development papers remain usable for ordinary
reproduction with disclosure, but cannot independently validate rules derived
from them. This applies across all stages, not just comparison with a held-out
report. Follow `references/validation.md` for calibration freezes, unused-table
evaluation, and fresh-paper/cohort validation. Existing assessment scope,
printed-digit tolerance, ACRe meanings, and plan-approval authority still apply.

## Assessment scope

Whole-paper assessment remains the default, including for Games. An explicit
caller request may add a **selected-target assessment** for named claims,
outputs, or estimates. Declare it from the original paper before inspecting
its dependencies or running code; a package's available files cannot choose
the target. Main-result choice follows `references/main-result.md`; an explicit
selected target remains a separate caller-defined scope. Follow
`references/assessment.md` § Selected-target assessment
for its declaration, separate namespace, and evidence rules. The canonical
whole-paper dossier, level, and table keep their existing meanings. A selected
result never substitutes for them or exports as a whole-paper grid criterion.

Carry the selected scope ID through the input/producer map, execution records,
reference comparison, README, and report. Preserve unresolved whole-paper
coverage even when the selected result is Fully. Changing scope requires
rechecking affected evidence before reusing categories or comparisons.

## Every stage

1. **Resume from evidence.** Read the existing folder, input hashes, source
   versions, target/scope declarations, approval/disposition records, and all
   written cumulative sections before acting. Perform stages 1..k in order;
   reuse valid computations rather than executing them again. Revisit missing,
   stale, blocked, or contradicted evidence when inputs, access, criteria, or
   declared targets change. Preserve earlier observations and freezes.
2. **Reread and reconcile.** After each stage, reread every section written
   so far, including the opening, assessment, and any earlier conclusions.
   Revise statements contradicted by later findings and record the old claim,
   new evidence, changed section, reason, and date in the existing README/report
   revision record. A computational freeze remains intact beside later diagnosis.
   On an unchanged resume, record the coherence check without duplicate results,
   another note, or an invented change to the level history.
3. **Evidence or nothing.** Every claim in `assessment.json`, `README.md`, and
   the report points to a file/line, URL/passage, or CSV row. Missing evidence
   stays unknown. Author files remain read-only; verify hashes, put fixes in
   new scripts, and preserve original outputs before diagnosis.
4. **Compile and update locally.** Follow `references/cumulative-report.md`
   after each stage, including at a scope or approval stop: build through the
   latest written section, with unexecuted rows visibly “not yet assessed — not yet run” and reasons.
   Update the same `report/<citekey>-replication.html` Zotero-note draft. Record
   build failure as a blocker, never as a compiled report. Collect AI provenance
   from inventory onward. The host's review/merge/publication gates still apply.
5. **Update README last.** Record stage/check status, requested and actual
   execution scope, elapsed effort/cost, coherence revisions, local build/note
   paths, and next blocker. Output one line per stage actually processed.

Sending author questions, reports, or notes and publication remain outward
acts under the host's existing gates. Local drafting grants no send authority.

## inventory

The goal is to grade the package from its contents, before running anything,
while retaining the original claim and source-based scientific premises under
`references/scientific-appraisal.md`. Scientific appraisal is distinct from
the computational grade.
Contents alone settle L1 to L3, L6 and L7; L4, L5
and L8 to L10 wait for `rerun`. Batchable: for a reading list, or for a team
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
   **main result** by the original abstract/introduction central claim, then
   its supporting table or figure, before package inspection or execution.
   Follow `references/main-result.md` for the source record, prospective
   motivated ties, proportionate advisor support, and optional official
   Highlights/Key findings under the blind source boundary. If full text and Zotero are unavailable,
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
   Inspect and flag scraper/API/download acquisition producers under
   `references/acquisition.md`; retain their actual replay status separately
   from package ingestion and any proposed temporal extension.
4. **Grade.** Account for every grid criterion exactly once as established,
   examined but not established, or unexamined, with blocked reasons where
   applicable (`references/assessment.md`). An empty `criteres` is valid only
   with that full dossier. Inventory the whole paper, including applicable
   appendix outputs and applicable empirical footnote results, for package
   completeness under § Empirical footnote applicability in that reference;
   bibliographic remarks and unquantified assertions remain distinct. An unseen paper blocks this
   coverage. Assess generated analysis inputs only under the inspected
   producer-chain conditions in that reference. Run criteria (`cra_*`,
   `crr_*`) stay `a_evaluer` until execution. Derive the level and six-row
   Reproducibility Table from the evidence; blocked unknowns remain unassessed.
   For an explicit selected target, additionally map its dependencies and derive
   its separately labelled provision rows, following `references/assessment.md`.
   Bind inspected inputs to manifest paths and exact representations; existing
   fetch/checksum requirements apply unchanged. Leave selected execution rows
   unassessed until their evidence permits a category.
5. **Open the report.** Start its introduction with the paper, substantive
   claim, method, chosen supporting result, package coverage, and unknowns.
   Select the template and compile under `references/cumulative-report.md`;
   update the single local note draft. Record source and AI provenance now,
   including unavailable identity/call/work-share evidence, for final disclosure.

## identify

Follow the opening with an **Identification** section. Work unattended using
source-based appraisal in `references/scientific-appraisal.md`: original claim,
argument/model, material facts, assumptions, and evidence limits. Use a strong
scientific reasoning advisor through the route skill, with the existing
causal review's distinct-perspective requirement where applicable; record actual
advice, disagreements, provenance, and unavailable perspectives. Apply blind
source exclusions to the advisor's brief and all retrieval before any lookup.

For causal claims, follow `references/identification-review.md`: source the
DAG and estimand, distinguish estimation fidelity to that graph from the
scientific credibility of the graph against other studies and common sense,
and explain material threats. For descriptive, predictive, and meta-analysis
claims, appraise the appropriate argument, model, and factual links without
forcing a DAG or causal label. Package/source/code inspection supplies evidence,
not permission for estimates during this stage.

Perform targeted verified checks of material source claims through permitted
primary evidence. State sources and passages actually inspected, the reasoned
judgment, disagreement, contradictions, and remaining gaps; unavailable evidence
cannot become confirmation. Finish with “Graph points or scientific premises
to support by a literature review before publication.” Deep literature search
or saturation is a separate request, outside this chain; no stop-and-offer is
required for these bounded targeted checks. Run no new estimates. Feed threats
and unresolved premises into challenge candidates, then reconcile all written
sections, compile, and update the same local note.

## rerun

The goal is to rerun the authors' code on the authors' data, then compare
every applicable printed statistic within the chosen execution perimeter. Connect implementation and data-audit evidence to
the claim, argument/model, and material facts under
`references/scientific-appraisal.md`; keep computational outcomes and
scientific conclusions separate.

### Choose execution scope before computation

Keep three distinct records: the canonical whole-paper assessment dossier,
any separately declared selected-target assessment, and this request's execution
perimeter. Scope limits execution, not the meaning of either assessment.

If the caller supplied scope, record it and proceed without asking again.
Otherwise ask in plain words: **main result** (inventory's chosen table/figure),
**I4R scope** (the assignment's authoritative requested outputs), or **whole
paper** (all applicable tables/figures, appendices, SI, and empirical footnotes).
Record the question time and the authorized default: main result after five
unanswered minutes. Do not compute before the answer or elapsed default.

Automatic continuation is optional. Where the runtime cannot resume on its own,
disclose that limitation, keep the question pending, compile the local report,
and wait for explicit resumption. On resume, use the actual answer if supplied;
otherwise, after verifying that five minutes elapsed, record and use the
authorized main-result default. Before then the question remains pending.
Never claim a timer or queued message resumed the session when it did not.

For an explicit I4R choice, resolve the perimeter from primary assignment
instructions/pre-games slides and the named template: record source/version,
exact target inventory, and coverage gaps before execution. The committed
General template defines main claims and reporting/category coverage; it does
not establish a universal Games table subset. Pilot Tables1–3 are not authority.
If the assignment-specific perimeter is unavailable or conflicting, report that
I4R scope remains unresolved and request the missing source/clarification;
never convert an explicit I4R choice to main-only by timeout. The five-minute
default applies only to the unanswered generic scope question.

Carry the chosen execution perimeter and source through README, coverage map,
comparisons, and report. Results outside it remain not yet run; limited execution
cannot establish unexamined whole-paper rows or a different selected target.

### Execute the chosen perimeter

Before choosing implicit implementation conventions by matching paper outputs,
apply the calibration freeze and disclosure in `references/validation.md`.
When the caller has authorized translation of a Stata package, consult
`references/stata-caveats.md` for version-qualified storage, expression, and
estimator evidence. An unavailable licence alone authorizes no translation.
A faithful Stata-to-Python reproduction can establish canonical CRA under
[the evidence contract](references/assessment.md#faithful-stata-to-python-cra);
native Stata execution is not a prerequisite. Disclose the actual method and
native execution status separately. This eligibility changes neither the
required scope and comparisons nor CRR eligibility.

1. Run `fetch.sh`. Rebuild the authors' environment and lock it: interpreter,
   packages and versions go into `manifest.json` `environment`.
2. Map each applicable published result, including tables, figures, appendices,
   and empirical footnotes supporting the target, to its source passage,
   producers, and required comparison statistics or assertion evidence under
   `references/assessment.md` § Empirical footnote applicability. Keep the
   whole-paper coverage map, with gaps, in `reproduce/README.md`. Carry any
   explicit selected scope ID and its required comparison outcomes separately;
   an unexamined whole-paper map stays unresolved, without expanding the
   selected execution request.
3. Run from the analysis data first (CRA), then from the raw data (CRR)
   where the package allows. A broken script is fixed in a new file. The fix
   and its reason are recorded. Ordinary faithful path/environment repairs may
   proceed under these preservation rules. A correction changing the empirical
   specification, sample, or estimate is a challenge proposal under existing
   approval, not an authorized repair (rule 7).
4. Write `out/reproduce.csv`: one row per compared statistic, at full
   precision. A statistic matches when it lies within half a unit of the
   paper's last printed digit. Never widen the tolerance to turn a
   discrepancy into a match. Retain produced estimates without authoritative
   printed numeric comparators in `out/auxiliary.csv`, with provenance in
   `reproduce/README.md`, under `references/assessment.md` § Auxiliary estimates.
   Auxiliary rows supply no comparison status or scoring evidence. For a
   published range or inequality, evaluate the actual assertion in separate
   `out/assertions.csv` evidence under § Published assertions in that reference.
   Preserve target, collection/extrema, and open/closed boundaries; ambiguous
   semantics stay unresolved. Assertion confirmation supplies no exact statistic
   match and cannot alone establish a canonical category. Keep all required
   numeric comparisons and the unchanged article tolerance.
   For trivial published statistics without author code, use
   `references/independent-recomputation.md` within this authorized rerun scope.
   Retain prospective triviality and separate production/strict-comparison
   evidence, including failed/not-run reasons; missing author code stays recorded.
   Independent evidence supplies no canonical or selected scoring success.
   When comparing two reproductions, use equality after the common deterministic
   three-significant-digit rounding rule in § Comparing two reproductions of
   that reference. Retain both full originals, rounded values, difference, and
   source/protocol/scope evidence in a separate ledger; missing or nonfinite
   inputs leave agreement unresolved. This supplies no article match or category
   promotion and does not rescore prior cases.
5. Update `assessment.json`. Set `cra_reussie` or `cra_echouee`, and
   `crr_*`, only when the main result's actual run/comparison evidence permits,
   with the CSV path as evidence. Missing execution stays unassessed; an
   execution perimeter that omits that result cannot establish its run criteria. For a
   faithful Stata-to-Python CRA, verify the model, sample, standard errors, and
   every required main-result comparison under the assessment evidence contract.
   Then
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
Whole-paper assessment remains the default; the execution-scope choice above
does not replace this selected-target contract or the canonical ACRe criteria. Follow these steps sequentially: each
freeze precedes the execution or diagnosis it governs.

1. Before executing code, commit a dated, hashed freeze of the authoritative
   paper targets, every required statistic and analysis/raw route, tolerance
   under the existing printed-digit rule, and comparison rules (including
   rounding and exact counts where applicable). Freeze any sourced assertion,
   target/quantifier, and boundary semantics separately from exact numeric
   comparisons under the assertion ledger contract. Bind the scope ID to the input
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
   For a separate scientific-impact conclusion, establish the cause and its
   claim-specific consequences from actual evidence under
   `references/scientific-appraisal.md` § Diagnose a discrepancy and its scientific
   impact. A documented typo or demonstrated numerical variation may support
   scientific confirmation beside the retained miss; small size alone cannot.
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

## challenge

The goal is to run fair robustness checks derived from identify. Carry material scientific-appraisal
gaps and anomalies from `references/scientific-appraisal.md` into the candidate
inventory with evidence and disposition; proposals await the existing approval.

Follow these steps sequentially: the inventory precedes selection, and the
approved plan precedes execution.

1. **Inventory before selecting.** Read the paper's robustness analyses,
   including applicable empirical footnotes, appendices, and supplied code.
   Apply `references/assessment.md` § Empirical footnote applicability to
   distinguish printed results from unquantified asserted checks.
   In `robustness/plan.md`, map each
   already-run check to its source and list excluded candidates with reasons
   (already run, unfair, infeasible, or outside scope). Unavailable appendix or
   code coverage stays a named gap. Every code anomaly logged by `rerun`
   enters the candidate list, with its disposition and evidence; an anomaly
   does not by itself establish a coding error.
2. **Draft the plan** from the material identification threats and unresolved
   scientific premises, using the rules' menu (`references/rules.md`) and the
   design-specific candidates in `references/robustness-menus.md`. Propose
   additions the paper does not already run. Link each to its identify threat
   or premise and the evidence it would discriminate. Include at least one
   fair main-result check outside the paper's statistical frame: a justified
   model-independent comparison, different design on the same data, or derived
   implication of the same hypothesis. Explain its assumptions and relevance;
   if unavailable or infeasible, record the blocker and seek a fair alternative
   rather than claiming the obligation met. A robustness check asserted in the
   paper without numbers or code is eligible for the plan and cannot be rejected
   as a duplicate on that ground. Propose it when it bears on the main result;
   the authorized approver may reject it for another explicit reason. Proposal does not
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
   approval before execution under the changed plan.
4. **Check approval.** Follow `references/probe-approval.md`: retain author
   approval in file or conversation, or panel approval under explicit bounded
   campaign delegation, for the identified plan/version. Keep actual author
   signatures distinct from truthful approval transcriptions. Without valid
   approval or with unmet conditions, report the plan path and blocker, compile
   the local report/update the note, and stop. No timeout or silence supplies
   approval. Refusal remains a blocker, including on resumed requests for complete.
5. **After approval**, write one script per check under `robustness/`. Each
   appends rows to `out/robustness.csv` with `stage=robustness` and `spec`
   naming the alteration. A resumed challenge runs only checks with no valid results yet; inspect
   the disposition ledger first so a failure, block, or withdrawal is not
   mistaken for an unattempted check. Record every planned check's disposition
   in `robustness/plan.md`, including those that produce no CSV rows.

For validation against a held-out replication report, apply § Validation
exposure and calibration before reading it or preparing the plan. The executor
and plan approvers must not have read that report; retain the answer boundary
until results are frozen.

## complete

Finish the report using `references/cumulative-report.md` after processing all
prior stages. Reconcile every written section against the final available
evidence, revision record, and planned-check dispositions. Rewrite the
introduction last so its claim, scope, and findings agree with the body;
write the conclusion with separate computational and scientific judgments,
limits, unknowns, and questions for original authors (do not send them).
Finalize AI Disclosure from provenance collected since inventory: host and
harness repositories/commits, roles, actual model identities, calls, and work
shares where known; label unavailable evidence rather than inventing it.

Compile the final local report and update the same local note draft. If scope,
execution, approval, or a build remains blocked, disclose the incomplete stages
and leave their rows unresolved; a request for complete grants no missing
approval and cannot manufacture computations. Sending or publishing remains
the author's outward decision under host gates.

## Zotero note

Keep the independent reading note from `reading-note`. This workflow maintains
one cumulative local replication-note draft,
`report/<citekey>-replication.html`, with YAML frontmatter carrying `zotero_item`
under `skills/reading-note/references/template.md`. Every stage updates this
same file; resume does not create another note or publish intermediate drafts.
Historical preliminary/reproduction notes and frozen folders stay untouched;
no automatic migration, deletion, duplicate publication, or rescore.

After host review and merge, publish only through the existing host route:

```bash
python3 "$IDH_ROOT/scripts/zotero.py" publish-notes --project <host project> \
  --collection "<collection>" --dry-run <draft>.html   # then without --dry-run
```

Retain an existing child-note identity where the host publisher supports an
update; unresolved destination/identity stays pending rather than creating
duplicates. Publishing blocked or not authorized? Keep the local draft and
report the blocker.

## Temporary historical-name mapping

This table interprets still-open tickets only; it grants no aliases. Delete
it from current skills/docs once all old-name tickets close, with a final
search and recorded disposition. Git keeps history; frozen artifacts retain
the names/version that produced them, without migration or rescore.

| Historical ticket wording | Current stage meaning |
|---|---|
| assess | inventory; its scientific identification part is identify |
| reproduce | rerun |
| probe | challenge |
| report | output compiled at every stage; complete finishes it |

## Output to the user

Print one line per stage processed: the folder, the stage, the ACRe level before and
after, the table rows that changed, the discrepancy count from comparison
rows only (excluding independent, auxiliary, and assertion rows), separate
independent production and strict-comparison totals and assertion outcomes when
present under `references/independent-recomputation.md`, and the
next blocker and local report/note status. State requested and actual execution
perimeters separately from assessment coverage. Name any selected scope ID and its separately labelled changes.
For `challenge`, either the plan path awaiting approval or the checks run.
