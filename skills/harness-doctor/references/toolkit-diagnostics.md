# Toolkit diagnostics

Use these reading procedures and instruments for a named concern during an
author-called harness-doctor visit. They are reusable diagnostic options;
they are never routine health checks, scheduled sweeps, or merge gates.
Follow `doctor-practice.md` and `diagnosis-discipline.md`, including the
harness precondition and a positive control before interpreting silence.

## Dependency inspection

**Question.** Does a named helper's dependency contract match where and how
its skill expects it to run? Inspect the skill's call site and the helper
together; an import inventory alone cannot settle that question.

**Existing owners.** `authoring-skills.md` § Toolkit principles governs
bundled helpers: standard library by default; a third-party specialized tool
is optional and has a working standard-library or manual route alongside.
Harness `scripts/` tools instead use the locked environment under
`rules/coding-python.md` § Environment. `tests/test_deps_declared.py` already
checks declarations using AST imports and `tests/repo_sources.py` owns that
gate's source inventory. This diagnostic does not replace or expand the gate.

**Inputs and cost.** Name a bounded set of Python source files, their skill
call sites, and the applicable checkout. Read-only, seconds, no model call,
credentials, package installation, or inspected-code execution. The helper
needs Python 3.10+ and readable files. Explicit paths also accept extensionless
Python; shell heredocs and other languages require reading their own sources.
Known extra Python search roots may be supplied with `--local-root <path>`.
The default local search is each inspected file's parent, not the whole repo.

**Control first.** Run the fixture-based behavior controls:
`python3 -m pytest tests/test_check_imports.py` from the locked development
environment. They include a third-party sentinel, stdlib and local imports,
unavailable sources, dynamic calls, and the CLI's exit-zero contract. These
controls test the instrument, not live-tree dependency compliance. If the
controls cannot run or do not fire, report inspection unavailable; a manual
reading control can still establish the reading procedure below.

**Instrument.** From the checkout, with `IDH_ROOT` set as in the skill:

```bash
python3 "$IDH_ROOT/scripts/check_imports.py" --root "$IDH_ROOT" \
  "$IDH_ROOT/scripts/skill_frontmatter.py" \
  "$IDH_ROOT/scripts/trace_events.py"
```

The JSON lists direct imports with line, classification, and evidence. It
identifies bundled-helper, harness-tool, or unclassified policy perimeters.
Findings and unavailable files exit zero: this is an instrument. Never read
its exit status as a clean dependency bill. An unclassified path needs a
human reading of its deployment contract before any policy judgment.

**Interpretation.** The example should identify `yaml` as a third-party
candidate in `skill_frontmatter.py` and direct stdlib imports in
`trace_events.py`. The former belongs to the harness's locked environment;
its presence is not itself a violation. Follow local import candidates to
establish their prerequisites if the complaint requires it. Record the
interpreter, required packages/versions, system commands, and services from
the actual call path and environment declarations; mark unexamined items
unavailable. Judge exceptions against existing guidance, without inventing a
registry. Propose the smallest correction only when evidence establishes a
gap; a compatible dependency contract is a valid outcome.

**Limits.** AST imports include lazy function imports, which do not establish
optional availability. Dynamic call sites are hints, not resolved targets;
aliases and custom loaders can escape them. Local paths are candidates, not
verified runtime resolution. Transitive dependencies, installed packages,
versions, system tools, and services remain unexamined. Even a file with only
stdlib imports has these limits. Missing/unreadable/invalid sources are
unavailable and have no empty import list standing in for inspection.

**Manual route.** Without the helper or newly written code, read a small
known source containing `import json`, a real sibling import, and a known
third-party import. Locate each import, including those inside functions,
and verify those three cases remain distinguishable. Then read each named
source the same way: list module and line; classify against the inspecting
Python's stdlib documentation and concrete sibling/search-root paths; retain
unresolved names as candidates. Read dynamic loaders and the skill's launch
contract separately. Compare prerequisites with the existing policy above,
report inspected scope and unknowns, and propose only established fixes.
This takes minutes per source rather than seconds for a batch; it preserves
the same authorization and verification requirements.

## Recovery when helpers are unavailable

**Question and scope.** For the named workflow, what do its instructions let
an agent do when a helper is missing, cannot be used in this environment, or
runs and fails? Start from a bounded set of call sites and their referenced
recovery instructions. Reading takes minutes per workflow; it needs readable
instructions, not a working helper, transcripts, network access, or new code.
Do not run a mutating helper merely to see how it fails.

**Controls before the reading.** These synthetic instruction excerpts hold
the task constant: produce a status table from an authoritative manifest.
They test the reader's judgment, not a keyword detector.

| Excerpt | Expected judgment and reason |
|---|---|
| A: “Run the status helper on the manifest; use its table to mark the task complete.” | Known helper-only recovery gap: if the helper is missing, inaccessible, or fails, neither a completion route nor a safe stop/report is specified. The table is unavailable, not empty. |
| B: “Use the status helper. If unavailable or failing, read the manifest's item identifiers and recorded statuses, copy one row per item, preserve unknown statuses, and compare row identifiers with the manifest before reporting the table. Reading needs no further permission; mutations still require the original authorization.” | Adequate completion alternative for this synthetic task: inputs, decisions, output, coverage check, and authorization survive helper failure. It adds reading time, not invented statuses. |
| C: “If the helper cannot be used or fails, report blocked with the input identifiers and observed failure; stop before marking completion or changing anything. Hand off to the caller to restore access, then recheck the input and required verification before resuming.” | Adequate containment and handoff, with completion still blocked. A safe stop does not establish that a manual completion alternative exists. |

The reading control fires only if A is identified as a gap and B and C retain
their different outcomes. If those distinctions cannot be made, report the
diagnostic unavailable. Do not infer a live defect merely because an excerpt
resembles A: the actual workflow may delegate recovery to an explicit owner.

**Read the real contract.** Record the source locations for the call, its
inputs and expected output, and the owning recovery text. Follow references
before judging silence. Examine missing helper/interpreter, unavailable
permissions or service, and failing execution separately; a documented
unsupported-runtime answer does not cover every way the helper can fail.
For each case, trace the decisions and checks through to one of these
outcomes: verified completion by another route; continuation with an
explicitly omitted optional result; safe stop/handoff with completion
blocked; or an established recovery gap. State which failure modes remain
unexamined instead of upgrading an adequate route for one case into general
coverage.

Assess the same inputs, decisions, checks, outputs, authorization, and
verification as the normal path. A completion alternative must produce the
required result and retain its checks. A stop/handoff must preserve the
blocked status, identify the missing prerequisite and next owner/action,
and avoid claiming success. An optional omission must be permitted by the
workflow's own contract. If the helper might have changed state before
failing, preserve uncertainty about its effects; do not recommend blind
replay or bypass an authorization boundary.

**Bounded source walkthrough.** The following examples illustrate the
reading procedure; they establish text coverage, not executed recovery.
Re-read the cited sources on the checkout under examination.

| Source | Reading result | Evidence limit |
|---|---|---|
| `skills/raid/references/sitrep.md:50` and `:63` | The explicit `NOOP wake arm` branch replaces timed sitreps with reporting at wave boundaries and breaker events, and requires disclosure that the timed cadence is unavailable. This is a documented degraded cadence. | Does not establish recovery from a missing `runtime.py` file, or successful delivery of any wake. |
| `skills/merge/SKILL.md:119` and `:127` | Failed or unreadable forge reads stop the landing; an offline cached answer also stops it for a later fresh read. This contains the failed read while completion remains blocked. | No manual merge bypass is warranted. Source reading does not demonstrate the running helper or every launch failure. |
| `skills/hunt/references/session-start.md:31` | The disk-warning helper is explicitly optional: if unavailable, continue. The warning remains unobserved; continuing the session does not mean disk headroom was checked. | Does not make a required check elsewhere optional. |

For historical context,
`memory/journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md`
§ F1 records a skill-directory substitution that made the first helper call
fail with “No such file”. Current `skills/hunt/SKILL.md:14` distinguishes a
supplied directory from a file before deriving the helper root. The record
establishes a past launch failure; the current text addresses that recorded
input shape. Neither proves that every helper has a completion alternative.
No concrete correction to those workflows is established by this bounded
walkthrough; other helper-failure paths remain unexamined.

**Report and follow-up.** Give the complaint, checkout and inspected call
sites; confirm the control judgments; distinguish source reading, historical
records, and executed behavior. For each inspected failure mode report the
outcome, retained or missing checks, scope of authorization, and unknowns.
Supplement with narrowly relevant transcript evidence when available, but
missing or silent transcripts establish neither a working fallback nor its
absence. Without helper execution, label execution coverage unexamined.
Propose a manual route only for an established gap where completing the task
without the helper is feasible; an explicit safe stop/handoff can be the
appropriate correction. Keep any change with its owning workflow, preserve
its authority and verification, and re-read the same failure branch after a
correction. Do not turn this diagnostic into a blanket fallback rewrite.

## Unavailable evidence becoming false

**Question and inputs.** Did an actual claim turn a failed or unavailable
observation into false, zero, absence, or an all-clear? Use the existing
measurement and diagnosis guidance in `authoring-skills.md` § Toolkit
principles and `diagnosis-discipline.md`; this is a way to examine behavior,
not another rule or an automatic classifier. Name the complaint, permitted
sources, selection method, time window, runtimes, and bounded sessions or
spans before reading. A small authorized span takes minutes; no helper,
network call, or new code is needed when that material is already readable.

**Reading controls.** These synthetic contiguous observation/claim pairs
hold the requested inventory and query constant. The stated context is part
of each control, not missing evidence supplied by the reader.

| Observation, context, and actual next claim | Expected judgment |
|---|---|
| A: The inventory read returns “permission denied; inventory unavailable”. No other source or recovery intervenes. The assistant then says “The inventory contains no matching items.” | Unsupported absence: the failed read cannot support that inventory claim. This is the positive control for the target error. |
| B: A complete inventory read succeeds; the query and enumeration are verified, including a known matching-query control. The requested query returns a recorded count of zero. The assistant then says “No items match this query in this inventory.” | Genuinely observed zero within the specified inventory and query. A zero or the word “no” is not itself a defect. |
| C: The read fails as in A. The assistant then says “Whether any items match is unknown; the inventory could not be read. A successful read would permit the check.” | Explicit unknown with its missing prerequisite, not a false conclusion. |

Confirm A is detected and B and C remain distinct before judging real
material. A reader that flags every negative claim has not passed these
controls. A failed tool followed by successful independent evidence before
the claim also needs that intervening context; the earlier failure alone
does not establish a finding.

**Examination.** Read each selected span sequentially, because the actual
observation and any recovery constrain what the later claim means. Locate
the task's scope, tool call and actual returned result/status, the relevant
assistant claim, and the contiguous intervening context through any
correction or successful check. Keep stable source/session/turn or call-id
pointers for both ends. Preserve the claim's qualifications, attribution,
and source scope: quoted tool output, a hypothetical, and a model's own
assertion are different acts. A keyword search may locate a candidate;
neither a hit nor a content-free timeline decides it.

For each pair, ask what information the observer actually had, whether the
source was accessible and complete, and whether the claim exceeds it.
Verify any zero's coverage and positive control, rather than treating a
successful command exit as evidence of a complete search. If a tool itself
misclassified missing input as zero, separate that software observation from
the assistant's subsequent statement. Inspect the actual context before
attributing unsupported reasoning to the model; a software classification
bug is not automatically an unsupported model claim. Unclear result
semantics, missing intervening turns, or truncated messages leave the case
unresolved. Do not fill those gaps with a plausible reconstruction.

**Bounded availability example.** The committed historical digest
`conception/trace-open-coding-2026-06/d27c1566-c018-4f41-838e-05b153511a28.digest.md`
contains structural turn rows. `$IDH_ROOT/scripts/trace-digest.py` explicitly removes
user and assistant text and command arguments; those rows cannot establish
the observation/claim pair. The public review answer for PR 2246, recorded
on 2026-11-07 in `refs/notes/review` as
`rv-20261107-pr-2246-6645`, states a Codex seat's review result and limits,
but does not preserve its contiguous tool observations and reasoning turns.
It is a review record, not a substitute transcript. Neither artifact
supports calling the review's “Findings: none” an unsupported all-clear.

For that bounded set of artifacts, semantic transcript inspection is
unavailable, not an empty audit: the actual result/claim context is missing,
and private/local-restricted raw transcripts were not accessed. The scope is
those named artifacts only; no underlying session window or cross-runtime
coverage was inspected. Synthetic controls exercise the diagnostic, not
session incidence. `tests/test_trace_events.py`'s unpriced-cost control is
likewise software representation evidence, not a transcript finding. An
authorized contiguous excerpt containing task scope, returned observations,
claims, and intervening recovery would permit the semantic check; preserve
those details when removing sensitive content. Use existing
`transcript_spool.py`, `trace_events.py`, and `trace_timeline.py` for source
resolution where appropriate, within the permitted access boundary; do not
read or decrypt restricted archives to manufacture coverage.

**Report.** State whether the material was actually inspected or unavailable,
with the sample/window/runtime coverage, control judgments, selection limits,
and missing evidence. For a finding, cite both the observation and claim
pointers and the smallest context that settles their relation; keep private
per-session text out of tracked reports. Preserve counterevidence and
unresolved cases. “No instances found” is valid only for the semantic spans
actually examined after the controls fired; it does not establish absence
in unread sources, missing runtimes, or a larger corpus. Report the named
missing evidence and what would permit inspection when it cannot be done.

## Historical implementation-language choices

**Question and scope.** For a named implementation, where was its language
or entry-point choice made, what concrete trouble followed, and what change
would remove that mechanism? This is an on-demand reading diagnostic, not a
Bash/Python/Rust prescription. Start with a bounded set of tickets, commits,
and source paths. Reading takes minutes per case; inert controls take seconds
with Bash and Python's standard library. No credentials, services, private
archives, or original session transcripts are needed for the examples below.

**Locate the decision.** Read the governing workflow, ticket, and relevant
before/after source sequentially. `skills/raid/SKILL.md` § Imagine opens
alternatives and § Plan requests actions and tests. `skills/hunt/SKILL.md`
§ Plan chooses the implementation route; its Execute section permits
replanning when evidence contradicts it. These are opportunities to make or
revise a language choice, not proof that any historical choice happened in
one particular phase. Existing project files and tool availability may also
constrain an executor's choice. Find the actual ticket action, design note,
commit rationale, or authorized session evidence that records it; otherwise
mark the decision location or rationale unknown. Git records an implementation
and stated rationale, not the executor's unrecorded reasoning.

**Controls before diagnosis.** Keep the intended output and input contract
fixed, then distinguish a representation mechanism from a domain-logic
error. Run only inert constructed fixtures, with host startup hooks disabled.
The following inputs derive from public source mechanisms, not recovered
private session inputs.

| Control | Reproduction and expected distinction |
|---|---|
| Empty middle field | Use the literal TSV record `17\t\tQk9EWQ==`. Bash `IFS=$'\t' read -r a b c` puts the encoded body in `b`, losing the empty title. Python `csv.reader` with tab delimiter preserves the empty middle field. Also try Bash `IFS='|' read -r a b c` on `17||Qk9EWQ==`: the smaller representation repair preserves it too. The alternative parser removes this mechanism; migration is not the only remedy. |
| Domain predicate | With the literal state `activating`, compare Bash's `[ "$state" = active ]` and Python's `state == 'active'` against the intended running states `active` and `activating`. Both predicates wrongly reject a running state. A language change alone leaves that error intact; correct the state contract. No real service is queried. |
| Shell/Python argument bridge | Give an outer Bash command the argument `fixture-root`, then invoke a Python stdin heredoc without forwarding that argument. Python's `sys.argv[1:]` is empty. Forward it explicitly with `python3 - "$1"` and the value arrives. A direct Python entry point also avoids the bridge, but explicit forwarding repairs the existing design. |

The control succeeds when the reader observes both the removable parsing or
transport mechanism and the logic error that survives translation, while
retaining a smaller same-language repair as a candidate. It does not decide
which language a real project should use. Record the constructed inputs,
commands, environment, and observed results; do not label this a replay of
the original incident.

**Bounded committed cases.** Read the named commit and its parent with Git;
use `git show`, never overwrite current source to reconstruct history.
These cases supply actual implementation history even where session reasoning
is unavailable.

| Evidence | Recorded trouble, choice, and limit |
|---|---|
| `a8c14201`, ticket 0515, historical `gen-skills-catalog.sh` | The shell's directory argument was never passed to its Python heredoc, leaving the Python default path in use. The commit repairs the bridge through an environment variable and replaces guessed YAML values with parsed YAML. Those are distinct mechanisms; the bridge repair retained the wrapper. |
| `cbc44c65`, ticket 0531 § Actions, item 3 | The ticket explicitly leaves the shell-wrapper versus Python-entry-point decision to implementation. The commit chooses the importable Python entry point so catalog consumers can share frontmatter extraction instead of maintaining divergent copies. The old wrapper already contained Python; the benefit is shared importability and removal of the wrapper boundary. The commit records a byte-identical catalog comparison; that is a historical record, not a newly measured render. |
| `afd44bc7`, ticket 0903, `skills/roar/check-close-claims.sh` | An empty title in a tab-delimited record would shift the encoded body into the title field. The commit repairs the format in Bash using encoded title/body fields joined with a delimiter outside their alphabet. Current source retains that format. This supports the smaller repair and does not establish a need to translate the script. |
| `3baf733d`, ticket 0951, historical `read-index.py` | A Python regex dropped index entries with bracketed titles. The recorded repair changes the grammar and rejects partial parsing within Python. Its surviving literal example, `- [A test [green] for a reason](x.md)`, permits checking the regex mechanism without reading anyone's memory. The existing language did not prevent the defect. |

For the first case's current successor, inspect
`$IDH_ROOT/scripts/gen_skills_catalog.py` and the shared frontmatter helper;
for the record-format case, inspect `skills/roar/check-close-claims.sh`.
The inert argument/empty-field controls reproduce their source-derived
mechanisms; they do not rerun those historical workflows or prove original
session intent. The original multilingual-JSON anecdote is not established by
these cases and remains unverified. It does not make this committed history
unavailable. The inspected cases already carry targeted repairs; no additional
current rewrite is established by this walkthrough.

**Judge the counterfactual.** For each real candidate, identify the failing
input, intended result, observed failure, and the exact language/library or
boundary feature that an alternative changes. Compare a local repair with
migration, including available parsers, dependency and deployment costs,
startup requirements, caller compatibility, and verification effort. A Rust
or Python proposal needs a measured relevant cost or demonstrated mechanism;
its reputation is not evidence. Preserve contrary cases and label missing
inputs, unsupported rationale, and unexamined behavior explicitly.

**Report and revisit.** Give the bounded sources, decision record and its
location, controls and reproduction limits, current disposition, and the
smallest supported proposal with its cost. A reasoned keep or no actionable
correction is valid. Recommend or apply a change only when the named evidence
supports it; keep it with its owning workflow and recheck the same failing
input afterward. A pure refactor needs the existing artifact-comparison route
in `diagnosis-discipline.md`. Do not infer an original language-choice mistake
from a later bug, or turn this diagnostic into a new workflow gate.

## CLI-wrapper comparison

**Question and scope.** For a named candidate, does its skill body add useful
behavior beyond the CLI and the project instructions, or merely relay them?
This is an on-demand reading comparison, not a skill-builder rule or a
removal sweep. Name the complaint, checkout, candidate set, underlying
command/source, and governing instructions before reading. A few candidates
take minutes; no CLI execution, usage measurement, credentials, or new code
is required. Titles, length, and command counts select no verdict.

**Reading controls.** Read actual bodies and their delegated owners, not the
historical label attached to a deletion:

- At `5f46eab6`, `skills/beat/SKILL.md:8–14` binds the current repository to
  `BEAT_PROJECT`, invokes `beat.py`, and relays its existing summary. The same
  revision's `./scripts/beat.py:615–633` owns project selection, `:1024–1070`
  owns locking and recovery, and `:1097–1102` produces that summary. This is
  a pure execution-wrapper control: no additional decision, check, recovery,
  or output transformation appears in the skill. Its named invocation still
  adds discoverability; thin behavior alone does not settle removal.
- `skills/dashboard/SKILL.md` §§ Report and Inspect is the adequate-skill
  control. `skills/dashboard/dashboard.sh` produces raw snapshots; the skill
  additionally requires full-state and delta tables, count-trend
  interpretation, closed-blocker handling, and changed-request inspection.
- As a counterexample to label-based deletion, read
  `5296365f^:skills/ticket-new/SKILL.md`: title normalization, validation,
  handoff sections, and tracker conventions occur in its body. Commit
  `9741b716` migrated the handoff template to `tickets/AGENTS.md` and tracker
  convention to `rules/workflow.md` before deletion. The deletion's “thin”
  label cannot substitute for comparing those surviving owners.

The controls fire when the reader distinguishes delegated execution from
additional judgment and preserves unique conventions and discoverability.
If a historical object or delegated source is unreadable, identify that
control as unavailable; do not substitute a title-based classification.

**Comparison.** Follow each skill's references and the CLI's documented or
source-defined contract. Compare decisions, checks, recovery, output
contract, and discoverability separately. For each, cite its owner and mark
what is unique to the skill, duplicated in project instructions, delegated
to the CLI, or unexamined. A one-command skill may add needed judgment; a
long body may duplicate existing instructions. A delegated responsibility
is not missing merely because the skill does not repeat it. Include input
selection, authorization, failure outcomes, and output interpretation in
the comparison; do not infer equivalence from the happy path alone.

**Bounded current reading.** Re-read these three candidates on the checkout
under examination. The following source comparison establishes no current
deletion candidate and makes no claim about the rest of the catalog.

| Candidate and compared owners | Added or delegated behavior; disposition |
|---|---|
| `dashboard`: its SKILL.md §§ Report/Inspect versus `dashboard.sh`, `tickets/AGENTS.md`, and `skills/merge/SKILL.md` § Gating tiers | The script gathers snapshots; the skill adds contextual delta reporting and request-claim inspection. Generic ticket and gate instructions do not supply that dashboard report. Retain. |
| `zotero`: its SKILL.md §§ A scraped identifier is a hypothesis / Output to the user versus `$IDH_ROOT/scripts/zotero.py` lookup/creation code and `rules/zotero.md` | The helper searches identifiers/titles and compares files; the skill adds document-own-title/author verification, rejection of cited-work identifiers, metadata rebuilding, reprint-year judgment, and per-item/rerun reporting. The rule owns library authority. Retain. |
| `reviewers`: its SKILL.md and `skills/reviewers/references/live-route.md` versus `$IDH_ROOT/scripts/runtime.py`, `skills/route/`, `AGENTS.md` / `rules/workflow.md` review instructions, and `scripts/coaching/references/replay.md` | Runtime dispatch and model choice are delegated; the skill defines bounded review requests, revision/identity provenance, discovery, and unavailable/integrity reporting. Frozen-board replay is a different task, not a substitute live-review CLI. No single equivalent command is established. Retain. |

**Report and disposition.** Preserve the complaint, inspected revisions and
sources, control judgments, comparison by dimension, evidence limits, and
unexamined references. Source reading does not measure invocation frequency,
user benefit, runtime execution, or all current skills; missing evidence
cannot establish redundancy. No such measurements are prerequisites for this
bounded diagnostic. Propose deletion only when the comparison establishes
redundancy and identifies where every required behavior and discoverable
entry point survives. Move a unique fact to its owner before proposing
removal, and retain an unresolved candidate when that preservation cannot
be shown. Preserve counterevidence and give the smallest supported proposal;
no automatic deletion, title-based purge, or new general rule follows.
