# Ticket 1080 live semantic acceptance

The change keeps project runner discovery intact and repairs semantic rule
location discovery, actual routed worker execution, completion validation and
blocking-finding verdict mapping. Contract tests are supplementary: they do
not execute future versions of the skill. The retained execution records prove
only this recorded invocation of the exact skill hash.

## Reproduce the neutral fixture

Use a fresh temporary directory as `fixture`; copy
`tests/fixtures/adherence-semantic/` into it. Initialize Git with branch `main`.
Before its initial commit replace `scripts/check-tree.sh` with:

```bash
#!/usr/bin/env bash
set -eu
git rev-parse --is-inside-work-tree
```

Commit the initial four files, create branch `candidate`, restore the archived
`check-tree.sh`, append the following line to `rules/worktrees.md`, then commit:

```
Apply this rule to every worktree detection script.
```

Invoke the complete modified skill with argument string
`candidate worktree=<fixture>`. Supply its absolute worktree SKILL.md path and
verify its SHA-256 before execution. Give the caller no defect description.
The fixture's declared `make syntax` runner intentionally checks syntax only;
it cannot substitute for the semantic worker.

## Execution and limits

The first outer attempt misread the literal branch name `candidate` as a
placeholder and stopped for missing arguments. The same outer seat resumed
when the branch parsing was clarified; no rule or defect hint was supplied.
The resumed invocation's worker returned a concrete finding but omitted its
explicit severity field. Its optional same-session normalization failed because
the transport could not resume that session. This attempt is invalid, even
though it found the defect. A second complete neutral invocation requests the
contract's exact worker schema and supplies the accepted run below.
Sanitized native execution extracts live in `adherence-semantic/outer.jsonl`
and `worker.jsonl`; `evidence.json` records the compact result and links their
actual launch, completion, loaded skill, and identity observations. User/account
metadata, encrypted reasoning, unrelated runtime instructions and rate limits
are omitted. No worker identity is inferred from its own self-description.

The accepted run loaded
`/tmp/idh-raid-1080-prep/skills/verify-adherence/SKILL.md`, SHA-256
`4435caf5dedc0bd8e1ac08832a19eb5b4a1347e722931e4741c90e32a6d9a5db`.
Its outer native session ran Sol 6.1 at medium effort, as observed in the
runtime `turn_context`. The distinct headless worker ran Haiku 5.5, Anthropic
family, as observed in `modelUsage` (effective effort unavailable; medium was
requested). The worker completed in 20.946 seconds, costing $0.0143562;
outer invocation to validation checkpoint took 81 seconds. Actual token usage
is retained in the worker result. The prior invalid worker cost $0.00491546.

`make syntax` passed. The accepted worker explicitly returned
`severity: blocking`, `scripts/check-tree.sh:3`, and `suggested_test`; the
outer verdict is `adherence: FAIL` with no infrastructure escalation.
The outer rejected an unsupported nit alleging missing mechanical enforcement,
and a separate proposed test that would swallow its failure. Those rejected
items remain in the unmodified worker output; they do not weaken the verified
blocking finding. Worker self-reported orchestration metadata is ignored;
the distinct process launch/completion records establish execution.
