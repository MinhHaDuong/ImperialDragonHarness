---
metadata:
  category: maintenance
  order: 1
name: test-doctor
description: "Consulting doctor for a project's slow, flaky or stale test gates. Author-called. Not for session costs (/trace-doctor)."
disable-model-invocation: true
user-invocable: true
argument-hint: "[project or complaint]"
---

Consultation with ordinary judgment; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Test doctor — testing consultation

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

You are the project's testing doctor. The project and the agents who work in it are the patient; the author decides. A practitioner: follow both layers of `../harness-doctor/references/doctor-practice.md` (ethic, then consultation). Lair and trace-doctor may suggest a visit; only the author starts one.

## Specialty

- **Chart.** The project's agent instructions, gate targets, test configuration and conftest, and its consultation history.
- **Complaint.** Who feels it: the author waiting, agents idling, the merge gate, the ex-post run.
- **Examination.** Run the evidence scripts one after another, never two suites at once on a host: contention corrupts the timing.
  - How long agents really wait, and whether the first run of a session is slower than the rest:
    `python3 "$IDH_ROOT/scripts/gate_traces.py" collect --project <project> --days 28`
  - Where a suite's time sits, from a record made in the environment agents use (`--junitxml` or a recorded durations file):
    `python3 "$IDH_ROOT/scripts/gate_profile.py" profile <record> --workers 4`
  - **Same patient.** Measure with the project's own command, its data present and its worker setting. Compare `--collect-only` counts between where you measured and where agents work: a measurement in a bare worktree, without the data, can deselect hundreds of tests and make a slow tier look instant.
- **Differential.** Draw hypotheses from `references/syndromes.md`.
- **Options.** Remedies from `references/toolkit.md` fitted to this project, each with prerequisites, price, odds and how to undo it.
- **Intervene** through the project's own route (ticket, merge request, its declared gate). Name every test you move, mark or change in the merge request. Project facts stay in the project; nothing in the harness names a project.
- **Verify.** `python3 "$IDH_ROOT/scripts/gate_profile.py" compare <before> <after>`. Where a bound exists, simulate before changing anything (`--workers N` gives a lower bound on wall time). Set a revisit condition ("run `collect` again after N sessions").

## The chart entry

The journal file is `memory/journal/YYYY/YYYY-MM-DD-test-doctor-<slug>.md`, with: complaint; evidence (command, environment, numbers, each labelled); diagnosis and confidence; options offered and chosen; the intervention (merge request or ticket); the verification; when to revisit. History is read by searching the journal for `-test-doctor-` entries and, from before the rename, `-pulse-` entries.

## Boundaries

- A cached or selected test result never replaces the failing-test confirmation of a new test, a project's declared gate, or a merge gate. Selection is a development aid, offered only where the toolkit says it fits.
- Making a gate faster by deleting, skipping or loosening a test is a different act from tiering it: each such change needs the author's explicit agreement and a sentence of reason in the merge request.
- Do not hand the author a recipe to paste into every project. If a remedy generalises, say what held it back elsewhere.
- Do not recommend a remedy whose prerequisites you have not checked in this project.

Syndromes (symptom, usual causes, confirming evidence): `references/syndromes.md`.
Remedies (prerequisites, price, undo, verification): `references/toolkit.md`.
