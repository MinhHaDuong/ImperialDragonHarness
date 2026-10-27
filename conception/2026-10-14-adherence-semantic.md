# Ticket 1080 live semantic acceptance

The repair preserves declared project runner discovery, discovers project
rules, requires an actual routed semantic worker, validates completion and
maps a blocking semantic finding to overall FAIL. The caller may reject
unsupported worker findings, but cannot create findings or supply missing
worker severity, anchors or suggested tests.

Contract tests supplement live acceptance. They do not execute future skill
versions. Retained execution records prove the recorded source snapshot only.

## Reproduce the neutral fixture

Copy `tests/fixtures/adherence-semantic/` into a fresh temporary directory and
initialize Git with branch `main`. Before the initial commit replace
`scripts/check-tree.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail
git rev-parse --is-inside-work-tree
```

Commit the initial four files, create branch `candidate`, restore the archived
`check-tree.sh`, append a blank separator followed by the line below to
`rules/worktrees.md`, then commit:

```
Apply this rule to every worktree detection script.
```

Invoke the complete modified skill with argument string
`candidate worktree=<fixture>` in an empty-context outer seat. Supply the
absolute worktree SKILL.md path and verify its SHA-256 before execution.
Give the caller no defect description or expected verdict. The declared
`make syntax` runner checks syntax only; it cannot replace semantic review.

## Accepted execution

The final accepted run loaded
`/tmp/idh-raid-1080-prep/skills/verify-adherence/SKILL.md`, SHA-256
`70146986d93d312bbf76060821cee592e99cfd9f38e97d61f60b0d7b892c3099`.
Native outer session `01a139bf-563d-71b2-ae0d-153ffda57d84` was launched
with `fork_turns: none`. Its model and effort are observed in `turn_context`:
Sol 6.1, medium, OpenAI family. The actual caller invocation provided only
contract loading, neutral branch/worktree and evidence instructions.

`make syntax` passed. A distinct routed Claude CLI worker completed with
session `3f10718b-2941-4929-9da5-c8c444afce35` and result UUID
`260da837-39bb-407b-a983-0342956e4bca`. Runtime observations identify
Haiku 5.5, Anthropic family; medium was requested, effective effort unavailable.
The worker returned explicit `severity: blocking`, `scripts/check-tree.sh:3`
and a nonempty `suggested_test`. The full skill returned `adherence: FAIL`
with no infrastructure escalation. The caller preserved the finding verbatim
and rejected an auxiliary evidence entry with an unsupported line number.

Worker elapsed time was 12.238 seconds (rounded), with reported cost
$0.00180995. Actual timings, token usage and costs are retained in the
[evidence records](adherence-semantic/evidence.json) and
[worker runtime records](adherence-semantic/worker.jsonl).

## Evidence provenance and limits

[evidence.json](adherence-semantic/evidence.json) holds a caller-normalized
summary of the final emitted verdict, its loaded-source snapshot and previous
accepted runs. Supported aliases and the mechanical-runner summary are caller
annotations; the raw emitted verdict remains in outer.jsonl. The snapshot hash
checks that historical source, rather than requiring future versions to retain
an obsolete hash.

[outer.jsonl](adherence-semantic/outer.jsonl) contains selected historical
native extracts, the complete functional tool-call/result sequence of the
final empty-context outer, native identity and token-usage observations,
explicitly named annotations, and original generated check output. The final
sequence includes loaded path/hash, discovery, runner, route loading and
child launch/completion. Native launch metadata attests `fork_turns: none`;
the runtime encrypts the caller message in its native file. Its exact plaintext
is separately labeled as an annotation from the actual user-visible tool
invocation, rather than presented as native plaintext. Worker input is retained
verbatim and contains the complete project sources/diff without a defect hint.
User/account metadata, encrypted reasoning and unrelated runtime instructions
are omitted. Runtime worker identities do not come from model self-report.

Earlier invocations reused an outer seat after a branch-parsing correction;
those were warm outer runs with fresh workers, not empty-context executions.
The first narrative worker omitted severity and was marked invalid; optional
session resumption failed. Those records and the originally mistaken outer
normalization remain, with an explicit correction. The final accepted run
uses an empty-context outer and does not depend on those earlier attempts.

## Verification

Original machine-generated red/green/lint output is committed as
`development_check_output` records in outer.jsonl. The first fast gate failed
six focused contract checks, then passed after the repair. The review also
caught a weak `rules/` substring assertion: it now requires the discriminating
conventional-discovery clause, which the legacy contract does not contain.
