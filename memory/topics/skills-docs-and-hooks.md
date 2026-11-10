# Architecture: skills, catalog, docs, hooks and instructions

## Current guidance
- **Catalog is generated** from `SKILL.md` frontmatter by `scripts/gen_skills_catalog.py`; after a name/description/category/order change run `make skills-catalog`. `Not for`/`Use for`/`Use to`/`Keyword(s):` stay in `description:` as routing hints; a hand edit fails the drift check ([1861][source1]); category under `metadata.category` ([catalog][source2]).
- **Skill names** ([rulings][source14]): lifecycle names stay dragon-themed; object skills carry their directory's name (`/paper`, `/mission`, `/post`, 2026-11-09); only user-invoked skills get a name and resident card; internal step = script, else runbook, else reference ([1228][source3]). Cards: budget 7000 chars ([1129][source4]). The tracked skills census caps at 6300: `/post` took it to 6323 and three description trims to 6248, cap not raised [4afd][source15].
- **Skill case notes** (`memory/skills/<skill>.md`) are pushed at skill load and re-selected by smelt each run (tickets 1431, 1432); example `memory/skills/merge.md` ([design][source6], [raid 3d5ae7][source7]).
- **Rules loading per runtime** is measured in `rules/README.md` § Loading per runtime (re-probe 2026-11-01): Claude Code loads the resident rules every session and strips HTML comments; Codex and Pi get them via generated AGENTS.md files plus conditional (`paths:`) rules (1424) ([ruleset review][source8]).
- **Resident budgets are composed.** `tests/test_rules_resident_budget.py` caps loaded rules at 15186 chars, raised from 15100 only with a ticket (1497, the interface-ceiling sentence in `rules/guards.md`) [2358][source16]; a budget can pass per base and fail after a sibling merge: rebase, re-set, re-gate ([6958fe][source9]).
- **Rules diet** (PR 2137, 1410): procedure lives in `skills/hunt/references/`, route § Escalation and harness-doctor's diagnosis discipline; § Cycle holds Imagine → Plan → Execute → Verify → Celebrate. guards.md (PR 2142): tickets are the only channel into another project ([ruleset review][source10]).
- **No Imagine skill** (author, 1415/1417 closed 2026-11-10): raid Phase 2 runs the per-ticket reimagine at the lead's judgment and the Blind-Spot pass always; `design/design-note-template.md` gained a status line, a `needs-human` rule for a proposed note's ticket and "reproduce each number before recommending" [morn][source17].
- **Docs.** `docs/` is git-ignored staging; design history in `design/` (renamed from `conception/` by PR 2310, 1477; byte-identical blobs); the editorial-brief glob and gaze prose panel keep a transitional `design/ or conception/` until the projects' alignment tickets close (check ~2026-11-23) [1477][source18]. STATE capped at 40 lines. Propagation enforced: catalog drift, STATE cap, `tests/test_root_doc_paths.py` ([1945][source11]).
- **Instruction sweep.** 24 of 94 findings confirmed; rulings: no model names in instructions, no private memory store ([1622][source12]). **Hooks** output is declarative ([1545][source13]).
- **Taxonomy (author, 2026-10-30).** Rules are law, skills/scripts apply them, configuration regulates, memory is jurisprudence. A skill cites another skill or rule instead of paraphrasing its contract (1438) [rulings]. The government memo's cooldown ended with the author's triage (1369) [morn][source17].
- Wording pins in tests are removed on sight in a PR's diff (PRs 2367, 2386); some remain in `tests/test_ticket_sweep.py::test_skills_call_the_script` [2367][source19].
## Hazards

- Route skill lines 67 and 115 and `routes-recommendations-claude-code.md:24` still call 230K a hard floor without the interface-session exception; `rules/guards.md` does not define "interface session" (gaze considers, not fixed) [2358][source16].

## Open questions
- Stop-hook ship state unverified (1164 closed).

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../design/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../design/memory-v8/source-revisions.tsv).
- [doc-refresh-final-merge](../journal/2026/2026-10-19-doc-refresh-final-merge.md), [skills-audit](../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md), [stopguard](../journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md), [raid-1298](../journal/2026/2026-10-28-raid-1298-f1-notes-evidence.md), [readme-pr1853](../journal/2026/2026-10-28-readme-pr1853-f1-notes-gap.md), [f642df](../journal/2026/2026-10-28-raid-f642df-1326-opt-out-not-refusal.md), [f7fa41](../journal/2026/2026-10-28-raid-f7fa41-forge-leaks.md), [1485 mission](../journal/2026/2026-11-09-1485-mission-skill-hunt.md), [1483 paper](../journal/2026/2026-11-09-raid-1483-paper-skill.md), [de-risk](../journal/2026/2026-11-09-derisk-imagine-tickets-pr2333.md)
- Off the page, in their episodes: instruction-sweep lens rates (delegation 2/5, git 5/5), end-of-turn hook dry run, the earlier 18000-char cap (superseded by the loaded-rules budget), the 1440/1445 memo items [memo], prose duties per skill and the docs-visit slug ([1945][source11]), the night cap living in route [rulings].
[rulings]: ../journal/2026/2026-11-07-rulings-1437-1439-batched-questions.md
[memo]: ../journal/2026/2026-11-07-raid-d35fb4.md

[source1]: ../journal/2026/2026-10-28-catalog-reverse-import-pr1861.md
[source2]: ../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md
[source3]: ../journal/2026/2026-10-27-test-doctor-rename-1228.md
[source4]: ../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md
[source6]: ../journal/2026/2026-10-31-skill-case-notes-design.md
[source7]: ../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md
[source8]: ../journal/2026/2026-11-01-ruleset-review-and-diet.md
[source9]: ../journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md
[source10]: ../journal/2026/2026-11-01-ruleset-review-and-diet.md
[source11]: ../journal/2026/2026-10-29-doc-propagation-pr1945.md
[source12]: ../journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md
[source13]: ../journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md
[source14]: user-rulings.md#on-work-shape
[source15]: ../journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md
[source16]: ../journal/2026/2026-11-09-roar-pr2358-interface-context-ceiling.md
[source17]: ../journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md
[source18]: ../journal/2026/2026-11-09-conception-to-design-rename-pr2310.md
[source19]: ../journal/2026/2026-11-10-roar-pr2367-housekeeping-notes-pins-removed.md

## Fallback
