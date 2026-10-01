---
name: dream
description: "Consolidate one project's repository memory without proposing rules."
user-invocable: true
---

# Dream — project memory consolidation

Use `/dream <project-repository> [--dry-run]`. The project repository is the
write destination; the installed skill directory is never a destination.
Read its AGENTS.md and versioned `memory/DREAM.md`. If the repository, memory
convention or prompt is missing, report what is missing and stop. Do not create
a replacement store in the harness or use the legacy helper scripts: those
helpers target the old shared/native store and are not this workflow.

## Procedure

1. Read `memory/MEMORY.md`, relevant `topics/`, previous accepted dream reports
   and new entries in `journal/YYYY/`. Read native notes only as attributed
   sources when available; report unavailable sources. Native notes are not the
   canonical reference or a write destination.
2. In dry-run mode, report candidate thematic updates and contradictions, then
   stop without writes, branches or commits. Do not propose rules.
3. For a writing run, use an isolated project checkout and dedicated branch;
   leave the primary checkout and unrelated changes alone. Consolidate themes,
   conditions, exceptions and contradictions into `memory/topics/`. Link source
   episodes; distinguish hypotheses from supported observations. Update the
   short `memory/MEMORY.md` index. Never rewrite, move or delete journal entries.
4. Write a report in `memory/dreams/` listing sources and revisions, changes,
   unresolved questions, runtime/model and prompt revision. Preserve the text of
   native notes actually used in the report or a versioned appendix, adapted to
   the project's audience. A fingerprint alone cannot preserve a mutable note.
5. Check links, provenance and the diff. Commit only memory outputs on the
   project branch and submit a PR following its integration policy. Do not
   merge automatically. Preserve and report the branch if submission fails.
   Only accepted reports count as completed processing on subsequent runs.

## Authority and scheduling

Dream writes only `memory/MEMORY.md`, `memory/topics/` and `memory/dreams/`
within the project or its explicitly configured private companion. It does not
modify AGENTS.md, rules, skills, runbooks or tests, open crystallisation issues,
propose promotions, or write cross-project provenance into the harness.
Crystallisation requires a separate explicit user request naming its scope and
destination. A useful pattern or a reviewed memory PR is not that request.

A periodic invocation uses this same boundary and an isolated project checkout.
This skill does not install a timer. Missing paths or permissions are visible
failures; never fall back to the harness or restore/change its primary branch.
