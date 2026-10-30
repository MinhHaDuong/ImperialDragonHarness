# Architecture: skills, catalog, docs, hooks and instructions

## Current guidance

- **Catalog is generated** from `SKILL.md` frontmatter (`metadata.category`, optional `metadata.order`) by `scripts/gen_skills_catalog.py`; after a name, description, category or order change run `make skills-catalog`. Sentences starting `Not for`, `Use for`, `Use to`, `Keyword(s):` stay in `description:` as routing hints; the catalog omits them. A hand edit fails the skills-drift check; the 2026-10-28 one was imported back into frontmatter ([1861](../journal/2026/2026-10-28-catalog-reverse-import-pr1861.md)). Categories go under `metadata.category`: Codex rejects a top-level field ([catalog](../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md)). Imported descriptions contradicted three skill bodies; check them.
- **Skill names (author rulings 2026-10-20, 2026-10-29).** Lifecycle names stay dragon-themed; only user-invoked skills get a name and resident card; an internal step is a script, else a runbook, else a reference. Fix routing in descriptions; rename only when the name misleads (hoard to smelt). `/test-doctor` waived the theme as meta ([1228](../journal/2026/2026-10-27-test-doctor-rename-1228.md)). Skill cards: resident budget 7000 chars ([1129](../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md)).
- **Resident rule budget is composed.** `tests/test_rules_resident_budget.py` (now 18350) can pass per base and fail after a sibling merge: rebase, re-set, re-gate ([6958fe](../journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md)).
- **Docs.** `docs/` is git-ignored staging; design history lives in `conception/` (author ruling, [1744](../journal/2026/2026-10-27-docs-to-conception-pr1744.md)); hash-pinned records keep old paths. README carries no install text; STATE is capped at 40 lines (`rules/state.md`).
- **Propagation.** Enforced: catalog drift, STATE cap, `tests/test_root_doc_paths.py`. Prose duties: roar 6, lair 10, yawn 11, gaze docs perspective (3 of 40 reviews ran a docs seat; mandatory seat deferred by the author). No scheduled global audit; docs visits use slug `-docs-visit-` ([1945](../journal/2026/2026-10-29-doc-propagation-pr1945.md)).
- **Instruction sweep.** 301 Haiku/Sonnet agents confirmed 24 of 94 findings; delegation lens caught 2 of 5 planted defects, git lens 5 of 5. Author rulings: no model names in instructions, no private memory store ([1622](../journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md)).
- **Hooks.** Hook output is declarative (`rules/claude-code.md`). End-of-turn hook: design merged, dry run first, untracked spool ([1545](../journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md)).
- **Taxonomy (author, 2026-10-30).** Rules: self-sufficient law, no forge names. Skills and scripts apply them; configuration regulates; memory is jurisprudence. Crystallising a case into a rule is the author's act.
- **Government memo** (`conception/2026-10-30-harness-government.md`) is in author-set cooldown: no tickets, rule or memory-design edits from it; context only.

## Hazards

- None current beyond the open questions.

## Open questions

- Docs-visit items for the author (2026-10-29, not rechecked): doctor floor wording vs `workflow.md`; `git.md` restating roar step 10; North star in `state.md` vs ROADMAP.
- `conception/` to `design/` rename floated, undecided.
- What shipped of the stop hook is unverified: ticket 1164 is closed, `scripts/trace-stopguard.py` exists.

## Retired

- 15-file review breaker forcing the 42-edit split: breaker removed by PR 1614 (see raids page) (smelt 2026-10-30).
- `workflow.md` sending worktree naming to `claude-code.md`: the naming table now sits in `workflow.md` § Session start (checked 2026-10-30).

- "STATE capped at 20 lines": retired by `rules/state.md` (40 lines).
- "Generalist/Research grouping and AGENTS edits unmerged in docs-refresh branch": retired by the catalog PRs 1467-1472 and the current AGENTS.md catalog section.
- "`/pulse` skill": retired by the 1228 rename to `/test-doctor`.
- "Docs design history in `docs/`": retired by PR 1744.

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
