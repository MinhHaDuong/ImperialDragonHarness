# Adherence verdict

Arguments: `t1591-replicator-dispatch worktree=/home/haduong/.agents/.claude/worktrees/t1591-266508-21774`.
Declared mechanical runner inspected with `make -n lint`, then executed:
191 passed,3736 deselected. No manuscript references changed. Diff contains
only tickets and dispatch evidence; no rule/instruction files or architectural
change trigger semantic fallback. Sender's actual distinct parent payload
review is recorded separately and is not receiver acceptance.

```yaml
adherence: PASS
mechanical_runner: ran
escalation: null
semantic_review:
  applicable: false
  status: skipped
  reason: "Only ticket status and handoff evidence; no rule/instruction or architectural diff."
  rule_sources: [AGENTS.md, rules/guards.md, rules/git.md, rules/workflow.md, tickets/AGENTS.md]
  worker_id: null
  model: unavailable
  family: unavailable
  effort: unavailable
  route: null
  launch_evidence: null
  completion_evidence: null
mechanical_failures: []
semantic_findings: []
untested_rules: []
```
