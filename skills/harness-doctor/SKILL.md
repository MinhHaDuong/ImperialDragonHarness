---
metadata:
  category: session
name: harness-doctor
description: "Lint the harness's own skills and rules for contradiction and overlap; author-called, harness repo only."
disable-model-invocation: true
user-invocable: true
argument-hint: "[skill or rule to start from]"
---

Review with careful judgment on contradiction and ownership; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Harness doctor — lint the harness's skills and rules

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

The harness's skills and rules are the patient; the author decides. This skill
finds contradiction and overlap in their text, reads the lint script and each
runtime's own diagnostics as evidence, and reports.

## Stance

- **Called, never self-started.** Only the author starts a run. No skill,
  hook, schedule or session start invokes it.
- **Harness only.** It examines the harness's own text, never a project's.
- **Every runtime alike.** No runtime is the reference: run what each ships,
  cheapest first, and report what could not run as unavailable, never clean.
- **Point, do not restate.** The rules a skill must follow live in
  `references/authoring-skills.md`; what the doctor looks for lives in
  `references/checklist.md`; the research behind both in `references/evidence.md`.
  Cite them in findings instead of paraphrasing.
- **The author decides.** Report and propose; change nothing unasked.

## Procedure

Sequential-blocking: each step selects what the next one reads.

0. **Refuse outside the harness.** Run `bash "$IDH_ROOT/scripts/harness_here.sh"`
   from the current directory. On non-zero, relay its one line and stop.
1. **Descriptions first.** Print the catalog with
   `python3 "$IDH_ROOT/scripts/gen_skills_catalog.py" "$IDH_ROOT"` and read the
   conditional table of `rules/README.md`. From descriptions and rule summaries
   alone, list the pairs that may overlap: same act, same decision, same
   artifact. With an argument, start from that skill or rule and its neighbours.
2. **Full bodies for those pairs only.** Read both texts of each listed pair,
   plus any rule body they cite. Do not read bodies with no overlap candidate.
   Look for the checklist's two judgment items: contradiction, and a skill
   presuming or paraphrasing another's responsibility.
3. **Mechanical lint.** Run `python3 "$IDH_ROOT/scripts/skill_text_lint.py" --root "$IDH_ROOT"`.
   Its stdout is JSON; read `.findings[]`, each `{file, line, check, text}`.
   It always exits 0 and is an instrument, not a gate. Judge every hit
   against `references/checklist.md`: keep it, or dismiss it with a word of
   reason (a date in a command example, a template).
4. **Runtime evidence.** Run the diagnostics in `references/runtime-diagnostics.md`
   for every runtime, in its order, one at a time. Lines marked as spending
   model usage need the author's agreement and a cost cap. For each runtime,
   record ran (with what it said that bears on skills), or unavailable (with
   why). A runtime that ships nothing is recorded as such against the
   control the reference names.
5. **Report.**

## Findings

Each finding names **both files and the conflicting lines**
(`path:line` on each side), says which rule or checklist item it breaks, and
proposes the smallest fix. A finding inside one file names that file twice.

Sort findings by the severity floor (`rules/workflow.md` § Autonomous action,
"Severity floor"): one that blocks a merge, corrupts state or misleads a
model into a wrong act becomes a ticket, filed on a branch through the
harness's own route; the rest are reported in the run, not ticketed.

The report has four parts: findings above the floor (with their tickets),
findings below it, dismissed lint hits (count and reasons), and the runtime
evidence table (runtime, diagnostic, ran or unavailable, what it showed).

## The record and retirement

After each run, write a journal entry in the harness's repository memory,
`memory/journal/YYYY/YYYY-MM-DD-harness-doctor-<slug>.md`, with `Date:` and
`Project:` headers, the run number, the count of findings above the floor,
and the tickets filed. Find earlier runs by searching the journal for
`-harness-doctor-` entries.

When the last three consecutive runs found nothing above the floor, ask the
author whether to delete this skill: the lint script and the edit-time rule
may then be enough. Delete only on the author's answer.
