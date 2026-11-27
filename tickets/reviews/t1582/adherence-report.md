```yaml
adherence: PASS
mechanical_runner: ran (make -n lint; make lint; 191 passed)
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: substantive assertion evidence contracts require semantic checking beyond lint
  rule_sources: [AGENTS.md, rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/lang/en.md, rules/prose/_all.md, skills/harness-doctor/references/authoring-skills.md]
  worker_id: 01a21cea-8b61-7390-b0fd-b4fd5b764e8b
  model: gpt-6.1-sol
  family: openai
  effort: medium
  route: native subscription codex exec read-only
  launch_evidence: redacted CLI header in adherence-semantic.md
  completion_evidence: valid reviewed_rules and empty semantic_findings; CLI exit 0
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

Reference resolution skipped: no changed .tex/.qmd/.bib. No trace supplied.
Required complete lint and fast tiers ran; no scoped pass is called full.
Fast tier: 1966 passed, seven existing deprecation warnings. No wording-pin tests.
The scenario audit supplies a positive control, boundary, and counterexamples.

First native semantic launch: failed/not-run. Automatic approval review rejected
transmission of repository rules, tickets, and diff because it could not verify
specific authorization for that destination. It executed no reviewer and counts
as no review. Verification then read back origin as the PUBLIC
MinhHaDuong/ImperialDragonHarness repository; the parent handoff explicitly
required native subscription/private review and recorded author raid authority.
The bounded same native read-only call was retried with that evidence and
accepted. Only the completed process above satisfies semantic review. No
alternate transport, paid API, private source, or secret loader was used.
