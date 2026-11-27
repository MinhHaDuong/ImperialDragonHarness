```yaml
adherence: PASS
mechanical_runner: ran (make -n lint; make lint; 191 passed)
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: substantive eligibility contracts require semantic evidence beyond lint
  rule_sources: [AGENTS.md, rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/lang/en.md, rules/prose/_all.md, skills/harness-doctor/references/authoring-skills.md]
  worker_id: 01a21cdd-a058-7fd3-b02d-7af99d55f47f
  model: gpt-6.1-sol
  family: openai
  effort: medium
  route: native subscription codex exec read-only
  launch_evidence: semantic-raw header, workdir redacted in adherence-semantic.md
  completion_evidence: adherence-semantic.md; valid reviewed_rules and empty semantic_findings; CLI exit 0
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

Reference resolution: skipped, no changed .tex/.qmd/.bib. No trace supplied.
No scoped gate used; make lint and make check-fast ran their whole declared tiers.
make check-fast: 1966 passed, seven existing warnings. No wording-pin tests added.
