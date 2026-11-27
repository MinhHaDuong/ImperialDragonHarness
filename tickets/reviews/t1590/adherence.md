# Adherence verdict

Product reviewed:85ff8b30c4ddcd4a2353e14830d69391e26a5723 against
193d610faf3340e1cd29c6c64a16cf83cb908b54. Required semantic residue was
reviewed in an actual distinct parent context; full report and observed
identity limitation: `semantic-integration.md:8`. The evidence commit adds
only the completed reports and results; exact final-head gaze/gate remain
caller's work. The declared mechanical runner is Makefile:30–34 (`make lint`),
validated with `make -n lint`; no .tex/.qmd/.bib changed, and no optional trace
was supplied.

```yaml
adherence: PASS
mechanical_runner: ran
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: "Five-stage instruction rewrite and cumulative scope/approval/report boundaries require semantic review."
  rule_sources: [AGENTS.md, rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/prose/_all.md, skills/harness-doctor/references/authoring-skills.md]
  worker_id: /root
  model: unavailable
  family: OpenAI
  effort: unavailable
  route: native parent context, distinct from producer, no cross-family assurance
  launch_evidence: "Parent/root actual completed direct-message review of stable product85ff8b30c; no new nested review spawned."
  completion_evidence: tickets/reviews/t1590/semantic-integration.md
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

`verification.md` preserves exact commands, actual191-test lint result,1966-test
fast result, byte controls, scenario walkthroughs, selector skips, environment
attempts, and limits. No raw tracked command log is included. No mapped scoped
pass or completed merge gate is claimed.
