# Ticket 1585 adherence and integration

2026-11-27. Product head `626f4ac994d102445a3f5141345d5e4fb98d0db1`,
base `9a1667845a67bd6fd012a8f4de094599e690956b`.
Actual parent `/root` completed a distinct native semantic and single-wave
integration review and sent the report below before evidence commit. Observed
model and effort are masked, family OpenAI shared with producer; no lineage
independence or requested-pin inference. No nested reviewer was launched.
Parent reported full product diff/reference, relevant full SKILL/assessment,
project rules, authoring guide, and retained advisor report read. No edits or
project/forge mutation; `git diff --check` passed.

```yaml
reviewed_rules:
  - rule_section: "1585 exit1; paper-led central claim and prospective ties"
    evidence: "main-result.md:3-14 orders abstract/introduction claim→supporting output→record→package; :39-44 retains equal-centrality candidates and motivated cohort rule before inspection. SKILL.md:163-174 and assessment.md:88-97 propagate the same ordering; package availability cannot replace main_result."
  - rule_section: "1585 exit2; actual advisor and bounded judgment"
    evidence: "main-result.md:32-37 requires route-advisor for pivotal ambiguity/conflict with advice/disagreement/exposure/disposition. Existing tickets/reviews/rulings1575/advisor-design.md is an actual distinct-context completed report with masked requested/observed limits; recommendations are implemented without pretending fresh consultation or scientific signoff."
  - rule_section: "1585 exit3; official Highlights and blind boundaries"
    evidence: "main-result.md:16-30 crosschecks optional article-specific official Highlights against abstract/introduction/output, retains conflict/version/gap, rejects universal publisher claim, and applies source exclusions before opening page or advising; inaccessible Highlights do not create discovery authority."
  - rule_section: "1585 exit4; canonical/selected scope and legacy records"
    evidence: "main-result.md:46-51 preserves original blocked target, separate secondary evidence, unchanged tolerance/criteria/coverage and no historical reselection. assessment.md:326-327 explicitly distinguishes caller-defined selected target; unchanged main-result run and whole-paper table contracts remain. Prior1584 approval policy unchanged."
  - rule_section: "authoring-skills/prose; scope and diagnosis"
    evidence: "One shared linked reference serves both changed parallel units, role/capability language without concrete models/drivers/publishers, sequential order stated, uncertainty and unavailable evidence retained. Goal/table/narrative scan found no surviving package-led or universal-Highlights selection instruction. No helper/service/estimate/test pin introduced; diff --check passes."
semantic_findings: []
integration: "CLEAN: composes with1584 approval/exposure and1581–1583 numeric contracts; original result remains selected before package even when a secondary result is executable."
```

## Mechanical result and skill verdict

Live `verify-adherence` loaded for branch `t1585-paper-led-main-result` and
this worktree. No `.tex`, `.qmd`, or `.bib` diff: reference-resolution phase
inapplicable. No trace argument supplied: trace-path scan not invoked.
`Makefile` declares adherence via `lint`; `make -n lint` confirmed
`uv run --frozen python3 -m pytest tests/ -m adherence`.
`make lint`: 191 passed, 3736 deselected (11.75 seconds). The fresh fetch/rebase
confirmed base unchanged and product head unchanged. Declared runner ran with
TMPDIR unset, local UV/RUFF caches, and authorized elevation for fixture sockets.
No mechanical failures. Semantic review is required because skill instructions
changed; the completed distinct parent report above supplies it.

```yaml
adherence: PASS
mechanical_runner: ran
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: "Skill instructions changed; distinct parent semantic review completed."
  rule_sources: [AGENTS.md, rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/prose/_all.md, rules/lang/en.md]
  worker_id: /root
  model: unavailable
  family: OpenAI
  effort: unavailable
  route: "Native parent context distinct from producer; reused completed review."
  launch_evidence: "Native collaboration task tree /root → /root/raid_delivery → /root/raid_delivery/hunt1585; producer request and parent completion messages."
  completion_evidence: "Parent completion report on product head 626f4ac994d102445a3f5141345d5e4fb98d0db1, preserved above."
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

`make check-fast`: 1966 passed, 7 existing DeprecationWarnings (9.90 seconds).
`git diff --check`: passed. Scenario controls and boundaries are recorded in
`plain.md`; no prose wording tests were added. Full gate belongs to the caller's
merge candidate, not this worker's scoped checks.
