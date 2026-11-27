# IDH1594 adherence and validation

Product base: `daa5e8eaaf0150689e262385e645813380ecf19a`.
Reviewed product head: `fd518e5f3893767b586938b0dd17ba166a48f77a`.
Main base: `ca56550c5a6d99866a7e9b9338322dc6e5560567`.
Rebase before checks returned up to date. Later evidence-only commit records
these results; no later product changes.

```yaml
adherence: PASS
mechanical_runner: ran
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: skill instruction/reference contract changes require distinct semantic review
  rule_sources: [rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/prose/_all.md, rules/lang/en.md]
  worker_id: /root/raid1580_lead
  model: unavailable
  family: OpenAI (shared; no lineage independence)
  effort: unavailable
  route: orchestrator native distinct context
  launch_evidence: worker sent immutable c57f197b7 product/base/path review request through collaboration.send_message; then fd518e5f3 pointer delta
  completion_evidence: lead returned completed reviewed_rules/semantic_findings YAML for c57f197b7 and actual gitdiff/HEAD supplemental review binding fd518e5f3
mechanical_failures: []
semantic_findings: []
```

The distinct reviewer read the complete product diff, scenarios, binary evidence,
and independently extracted the committed DOCX source tables. Findings: none.
Review evidence by rule section:

| Reviewed rules | Actual reviewer evidence |
|---|---|
| Guards, scope, and author intent | report-style3–5,50–59,83–101 adds prospective presentation only; assessment278–283 distinguishes hesitation from missing evidence; no science, score, or publication authority |
| Captions and context, exit1 | report-style7–26 preserves R numbering, explicit article references, contextual wording, effect first, and qualified Brodeur naming |
| Categories and templates, exit2 | report-style28–59 retains source checklist/columns, marked addition, versions/use evidence; lead DOCX extraction corroborated rows; original binaries unchanged |
| Robustness, exit3 | report-style61–81 preserves same-data heading, truthful reproduced/not-run cross-references, signed-check counts and dispositions |
| Attribution and diagnosis, exit4 | report-style83–101 records source/period/denominator and unavailable history; requested pin distinct from served identity |
| Causal/noncausal appraisal, exit5 | identification-review57–70 adds captioned graph and threats table; verdict scale and approval/noncausal routes retained |
| Skill authoring, prose, and git | Shared reference linked in cumulative/rules/assessment and SKILL30; no frontmatter, model-tier, code, or binary change; scenarios rather than wording tests; owned branch and wave base |

## Mechanical checks and limits

`make -n lint` confirmed Makefile32–33's declared adherence runner.
`make lint`: initial run failed only the new reference pointer check (190 passed);
adding the direct SKILL pointer fixed it. Final run:191 passed,3736 deselected.
`make check-fast`: sandbox run had1769 passed and197 socket-fixture setup errors
(PermissionError creating sockets); elevated run passed1966 tests with7 existing
deprecation warnings. Commands used `env -u TMPDIR`, own `.tmp/uv-cache` and
`.tmp/ruff-cache`, and `UV_LINK_MODE=clone`; `uv sync --frozen` completed.
`git diff --check` passed. No trace supplied; optional trace scan skipped.
Reference resolution of manuscript symbols is inapplicable: no tex/qmd/bib diff.
No tests added; no wording-pin tests. Scenario/source audit and template-byte
comparison are committed alongside this record. No full integration gate is
claimed; gaze/gate/merge belong to the orchestrator.
