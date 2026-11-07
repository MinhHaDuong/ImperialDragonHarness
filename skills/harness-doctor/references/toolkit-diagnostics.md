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
