# Ticket 1586 adherence and integration

2026-11-27. Product head `67ca68036e7e87dcc1791d39fe514faa41ed3d1b`,
base `c23896c09f745313d0e5efb338b5f8edc0e1841c`.
Actual parent `/root` completed a distinct native semantic and single-wave
integration review and sent the report below before evidence commit. Observed
model and effort are unavailable because runtime masks exact identity. Shared
OpenAI family supplies no lineage independence. Parent reports full product
diff and relevant context read, no edit/add/commit/push or forge mutation, and
`git diff --check` passed. No nested gaze or reviewer was launched.

```yaml
reviewed_rules:
  - rule_section: "1586 exit1; applicability by empirical meaning and declared scope"
    evidence: "assessment.md:138-155 includes body/table-note/footnote empirical support of declared target, records original source/version/link/computational applicability and excludes merely bibliographic notes with reason. Whole-paper inspection and selected perimeter explicitly separated at :143-147. SKILL.md assess/reproduce/probe/report and rules.md:26-31 propagate it across the logical unit."
  - rule_section: "1586 exit2; no invented comparator or category"
    evidence: "assessment.md:157-166 routes printed numeric results to existing tolerance, sourced range/inequality to published assertions with endpoint comparisons, and unquantified checks to existing probe approval. No invented number, match, predicate or automatic category; produced no-comparator estimates remain auxiliary. Probe inventory SKILL.md:342-344 preserves this distinction."
  - rule_section: "1586 exit3; evidence, applicability and prior cases"
    evidence: "assessment.md:149-155 distinguishes missing code/data, missing comparator and no-computation output; :168-172 retains omissions/unknowns and forbids automatic legacy inventory/rerun/rescore. Auxiliary parallel unit :663-670 now refers to applicability without pretending to settle other qualitative/tolerance questions. SKILL report:426-428 retains separate outcomes and scope."
  - rule_section: "authoring-skills; guards; prose; diagnosis"
    evidence: "Shared applicability contract links assess/reproduce/probe/report/rules; no model/runtime/driver pin, helper, pipeline or scientific estimate. Sequential existing workflow unchanged; numeric observation/assertion/inference/unknown distinctions explicit. Goals/table/narrative scan preserves previous1584 approval and1585 paper-led target selection. No wording-pin test introduced; diff --check PASS."
semantic_findings: []
integration: "CLEAN with1584–1585 and numeric base: selected run includes only applicable supporting footnotes while unrelated outputs remain whole-paper gaps; assertions cannot become matches or categories."
```

## Mechanical result and skill verdict

Live `verify-adherence` loaded for branch `t1586-empirical-footnotes` and this
worktree. No `.tex`, `.qmd`, or `.bib` changed: reference-resolution phase
inapplicable. No trace argument supplied. Makefile declares `lint` as adherence;
`make -n lint` confirmed `uv run --frozen python3 -m pytest tests/ -m adherence`.
Fresh fetch and explicit rebase confirmed the product and base unchanged.
The declared runner completed on that same base/head: `make lint` passed
191 tests, 3736 deselected in 12.34 seconds. No mechanical failure.
TMPDIR was unset, caches local, fixture socket access authorized. The semantic
phase is required because skill instructions changed; actual distinct parent
completion above supplies it.

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
  route: "Native parent context distinct from producer; reused actual completed review."
  launch_evidence: "Native task tree /root → /root/raid_delivery → /root/raid_delivery/hunt1586; producer request on product 67ca68036e7e87dcc1791d39fe514faa41ed3d1b and actual parent completion message."
  completion_evidence: "Actual parent report on the named product/base, preserved above; writer identity evidence separately in plain.md."
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

`make check-fast`: 1966 passed, 7 existing DeprecationWarnings in 10.16 seconds.
`git diff --check`: passed. Constructed positive, boundary, and counterexample
controls are in `scenario-audit.md`; no wording-pin tests were added. The
worker's lint and fast tiers are not the caller's full merge-candidate gate.
