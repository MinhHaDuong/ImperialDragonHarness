# Architecture: skills, catalog, docs, hooks and instructions

## Current guidance
- **Catalog is generated** from `SKILL.md` frontmatter by `scripts/gen_skills_catalog.py`; after a name/description/category/order change run `make skills-catalog`. `Not for`/`Use for`/`Use to`/`Keyword(s):` stay in `description:` as routing hints; a hand edit fails the drift check ([1861](../journal/2026/2026-10-28-catalog-reverse-import-pr1861.md)); category under `metadata.category` ([catalog](../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md)).
- **Skill names (author rulings 2026-10-20, 2026-10-29).** Lifecycle names stay dragon-themed; only user-invoked skills get a name and resident card; internal step = script, else runbook, else reference; rename only when the name misleads; `/test-doctor` waived the theme ([1228](../journal/2026/2026-10-27-test-doctor-rename-1228.md)). Cards: budget 7000 chars ([1129](../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md)).
- **Skill case notes** (`memory/skills/<skill>.md`) are pushed at skill load and re-selected by smelt each run (tickets 1431, 1432); mechanism: [memory page](memory-v8-governance.md), example `memory/skills/merge.md` ([design](../journal/2026/2026-10-31-skill-case-notes-design.md), [raid 3d5ae7](../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md)).
- **Rules loading per runtime** is measured in `rules/README.md` § Loading per runtime (re-probe 2026-11-01, sentinels): Claude Code loads the four resident rules every session and strips HTML comments; Codex and Pi get them via generated `~/.codex/AGENTS.md` / `~/.pi/agent/AGENTS.md` plus conditional (`paths:`) rules (1424) ([ruleset review](../journal/2026/2026-11-01-ruleset-review-and-diet.md)).
- **Resident budgets are composed.** `tests/test_rules_resident_budget.py` caps loaded text at 18000 chars (from 18350, author request); `scripts/resident_census.py` counts rules with comments stripped (cap 15100); a budget can pass per base and fail after a sibling merge: rebase, re-set, re-gate ([6958fe](../journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md)).
- **workflow.md diet** (PR 2137, ticket 1410): procedure moved to `skills/hunt/references/session-start.md`, `decomposition.md`, `skills/route` § Escalation, `skills/harness-doctor/references/diagnosis-discipline.md`; § Cycle added (Imagine → Plan → Execute → Verify → Celebrate; roar [Verify → Celebrate]). **guards.md rewritten** (PR 2142): tickets are the only channel into another project; context guard 230K in route and raid ([ruleset review](../journal/2026/2026-11-01-ruleset-review-and-diet.md)).
- **Docs.** `docs/` is git-ignored staging; design history in `conception/` (PR 1744); README carries no install text; STATE capped at 40 lines (`rules/state.md`). Propagation enforced: catalog drift, STATE cap, `tests/test_root_doc_paths.py`; prose duties roar 6, lair 10, yawn 11, gaze docs seat (deferred); docs visits use slug `-docs-visit-` ([1945](../journal/2026/2026-10-29-doc-propagation-pr1945.md)).
- **Instruction sweep.** 24 of 94 findings confirmed; delegation lens 2/5 planted, git lens 5/5; rulings: no model names in instructions, no private memory store ([1622](../journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md)). **Hooks** output is declarative; end-of-turn hook design merged, dry run first ([1545](../journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md)).
- **Taxonomy (author, 2026-10-30).** Rules are law, skills/scripts apply them, configuration regulates, memory is jurisprudence; crystallising a case into a rule is the author's act. **Government memo** in author-set cooldown (1369 open).
## Hazards

- None current beyond the open questions.

## Open questions
- Severity floor: workflow.md files tickets when a defect "blocks a merge, corrupts state, or bites the science"; harness-doctor triages "misleads a model into a wrong act" first. Ticket 1438.
- `conception/` to `design/` rename floated, undecided. Stop-hook ship state unverified (1164 closed).
## Retired

- 15-file review breaker forcing the 42-edit split: removed by PR 1614 (smelt 2026-10-30).
- "The naming table sits in workflow.md § Session start": retired by the workflow.md diet (PR 2137) — it lives in `skills/hunt/references/session-start.md`.
- "STATE capped at 20 lines": retired by `rules/state.md` (40 lines).
- "Generalist/Research grouping and AGENTS edits unmerged": retired by the catalog PRs 1467-1472 and current AGENTS.md.
- "`/pulse` skill": retired by the 1228 rename to `/test-doctor`.
- "Docs design history in `docs/`": retired by PR 1744.
- "Codex and Pi load none of rules/": retired same day by the 2026-11-01 re-probe (generated AGENTS.md files; 1424).

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [doc-refresh-final-merge](../journal/2026/2026-10-19-doc-refresh-final-merge.md)
- [catalog-grouping](../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md)
- [skills-audit](../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md)
- [pr1622](../journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md)
- [stopguard](../journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md)
- [raid-1298](../journal/2026/2026-10-28-raid-1298-f1-notes-evidence.md)
- [readme-pr1853](../journal/2026/2026-10-28-readme-pr1853-f1-notes-gap.md)
- [f642df](../journal/2026/2026-10-28-raid-f642df-1326-opt-out-not-refusal.md)
- [f7fa41](../journal/2026/2026-10-28-raid-f7fa41-forge-leaks.md)
- [case-notes design](../journal/2026/2026-10-31-skill-case-notes-design.md), [raid 3d5ae7](../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md), [ruleset review](../journal/2026/2026-11-01-ruleset-review-and-diet.md)
