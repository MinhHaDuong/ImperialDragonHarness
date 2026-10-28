---
metadata:
  category: maintenance
  order: 3
name: harness-doctor
description: "A harnessing expert. Can lint skills and rules for contradiction and overlap, and much more. Author-called, harness only."
disable-model-invocation: true
user-invocable: true
argument-hint: "[skill or rule to start from]"
---

Review with careful judgment on contradiction and ownership; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Harness doctor — a visit to the harness's skills and rules

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

The harness's skills and rules are the patient. A practitioner: follow both
layers of `references/doctor-practice.md` (ethic, then consultation), in the
manner of `skills/test-doctor/SKILL.md`; the specialty below is what differs.

## Precondition

Before any probe, run `bash "$IDH_ROOT/scripts/harness_here.sh"` from the
current directory. On non-zero, relay its one line and stop. This is a gate,
not a probe: it is never offered, skipped or priced.

## Specialty

- **Starting point.** With an argument, start from that skill or rule and its
  neighbours. Without one, ask what hurts; with no complaint, triage.
- **Harness only.** It examines the harness's own text, never a project's.
  The one exception is a shadowing question: `project_shadow.py` then reads the
  project's same-named skills and rules to compare them with the harness's.
- **Every runtime alike.** No runtime is the reference.
- **Point, do not restate.** The rules a skill must follow live in
  `references/authoring-skills.md`; what the doctor looks for in
  `references/checklist.md`; the research behind both in `references/evidence.md`.
  Cite them in findings instead of paraphrasing.
- **Writes** only its journal entry and the tickets the floor calls for.
- **Complaint or triage.** A complaint names where to look. With none, the
  default input is the skills and rules changed since the last
  `-harness-doctor-` journal entry (`git log --since=<its date> -- skills rules`);
  with no entry, the whole catalog, read by descriptions only. Triage orders the
  work by what costs most to be wrong about, before any probe runs: a
  contradiction that misleads a model into a wrong act first, then a skill
  presuming another's ownership, then mechanical lint, then runtime drift.

## Probes

A menu, not a sequence: launch a probe only when it separates live hypotheses.

| Probe | Answers | Cost |
|-------|---------|------|
| Catalog and descriptions: `python3 "$IDH_ROOT/scripts/gen_skills_catalog.py" "$IDH_ROOT"` and the conditional table of `rules/README.md` | Which skills or rules may overlap: same act, same decision, same artifact | Seconds; reading tokens; no credentials |
| Overlapping bodies: both texts of a listed pair, plus any rule body they cite | Contradiction, or a skill presuming or paraphrasing another's responsibility | Minutes; reading tokens per pair; no credentials |
| Lint: `python3 "$IDH_ROOT/scripts/skill_text_lint.py" --root "$IDH_ROOT" [paths]` | Mechanical hits: history phrasing, dates, ticket forms, project names, body length, long blocks | Seconds; no model usage; no credentials |
| Runtime diagnostics, per `references/runtime-diagnostics.md` | What each runtime loads and flags: shadowing, precedence, install health | About a minute each; spends lines need agreement and a cost cap; credential rules there |
| Stale skills: `"$IDH_ROOT/scripts/mammoth-audit.py"` | Which skills no session trace has invoked in 180 days, as removal candidates; aggregate counts only, nothing removed | About 45 s on 7,500 trace files (4.7 GB); no model usage; no credentials; reads `~/.claude/projects`, writes one JSON report under `~/.local/state` |
| Merge path: `python3 "$IDH_ROOT/scripts/trace_merge_path.py" --since <YYYY-MM-DD>` | Whether sessions run the reviews and gates a skill requires before they merge: each merging session classed gated, bookkeeping or no gate seen, plus verify-gate loads without `repo=`; read the unexplained ones by hand | Under a minute on a week of traces; no model usage; no credentials; reads `~/.claude/projects`, prints session ids and skill names only |
| Review trajectory: `python3 "$IDH_ROOT/scripts/review_trajectory.py" --since <YYYY-MM-DD>` | Which merged PRs show an approach not converging, a reviewer miss, weak coder output (`--coder-threshold`) or a month-over-month rise in late-finding severity; each class cites PR numbers | Seconds; no model usage; no credentials; needs `refs/notes/review` fetched locally, PRs reviewed after the finding-tag bar landed, and the round-1 heads in the clone; reads git only, edits nothing |
| Shadowing: `python3 "$IDH_ROOT/scripts/project_shadow.py" <project>` | Whether a project's skill or rule, named like the harness's, shadows it | Seconds; no model usage; only for a shadowing question |

The lint prints JSON on stdout: read `.findings[]`, each
`{file, line, check, text}`. It always exits 0 and is an instrument, not a
gate. Judge every hit against `references/checklist.md`: keep it, or dismiss
it with a word of reason (a date in a command example, a template).

Run runtime diagnostics one at a time, each under a limit of about a minute;
a timeout is unavailable. Never run a form that prints a credential; one that
refreshes a credential needs the author.

## Positive control

Before reading a probe's findings, fire it on its control (the rule:
`references/doctor-practice.md`):

- Lint: run it alone on `"$IDH_ROOT/tests/fixtures/harness-doctor/trace-doctor-SKILL.md"`,
  a frozen copy of a skill that must raise `body_lines`, `date`,
  `history_phase` and `long_fence`. All four must appear.
- Merge path: `tests/test_trace_merge_path.py`, whose fixture traces hold one
  session of each class, a gate run inside a subagent and a grep that only
  names the merge command.
- Review trajectory: `tests/test_review_trajectory.py`, whose fixture repo holds one merged PR
  per class, the reviewer miss derived from a round-1 line a later blocker cites.
- Runtime diagnostics: the control each runtime's section names.
- Reading probes: the known overlap of this skill with
  `skills/test-doctor/SKILL.md` (the shared visit stance the checklist
  records); a reader that misses it is blind.

A control that stays silent means the probe is blind: report that probe
unavailable. The report says, per probe used, that its
control fired.

## Findings and report

Each finding names **both files and the conflicting lines**
(`path:line` on each side), says which rule or checklist item it breaks, and
proposes the smallest fix. A finding inside one file names that file twice.

Sort findings by the severity floor (`rules/workflow.md` § Autonomous action,
"Severity floor"): one that blocks a merge, corrupts state or misleads a
model into a wrong act becomes a ticket, filed on a branch through the
harness's own route; the rest are reported in the visit, not ticketed.

Every proposal carries a price and odds, as the ethic requires.

The report gives: the complaint or triage input; the hypotheses and the
probes that separated them; the controls fired, per probe; findings above the
floor (with their tickets) and below it; dismissed lint hits (count and
reasons); the runtime evidence table (runtime, diagnostic, ran or
unavailable, what it showed); priced proposals with the recommendation; the
revisit.

## Journal and revisit

The journal is `memory/journal/YYYY/YYYY-MM-DD-harness-doctor-<slug>.md`, read
by searching for `-harness-doctor-` entries. For each ticket the last entry
filed, check whether it closed and whether the fix held: rerun the probe that
found it, on the same target. The entry holds the complaint or triage input,
the count of findings above the floor, the tickets filed, what the revisit of
earlier tickets showed, and the revisit condition.
