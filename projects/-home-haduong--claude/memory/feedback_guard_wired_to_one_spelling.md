---
name: guard-wired-to-one-spelling
description: "A gate that recognises one spelling of the action it guards is not a gate — enumerate every spelling, starting with the ones your own docs recommend"
metadata:
  node_type: memory
  type: feedback
---

The consumer merge gate (harness ticket 0900, 2026-09-10) counted reviews before
a merge. It recognised `gh pr merge` and nothing else, so
`gh api repos/O/R/pulls/N/merge -X PUT` returned

    allow :: Not a pull-request merge — the review gate does not apply

about a command that merges a pull request. Two layers were wrong, and the
outer one was worse: the handler's `if` filter was `Bash(gh pr merge *)`, so the
REST form never reached the script at all. A reproduction that pipes a payload
into the hook only exercises the inner layer and makes the coverage look
complete.

**Why it matters more than an ordinary miss:** the harness's own
`scripts/block-pr-merge-in-worktree.sh` prints that exact `gh api ...` command
as the *prescribed workaround* when `gh pr merge` refuses to run from a
worktree. The one path agents are told to take was the one path the gate could
not see. The bypass was not exotic; it was documented.

Same ticket family, same shape: `gh repo set-default` records the target in
`remote.<name>.gh-resolved`, and the resolver read `origin` while calling that
"a measurement of what gh would resolve". Under a fork topology it is a
different answer.

**How to apply.** When writing or reviewing a guard, list every spelling of the
action it guards before writing the predicate — porcelain and API form, short
and long flag, MCP tool and shell command — and grep your *own* docs and guards
for a spelling they recommend. Check the wiring separately from the logic: a
`matcher`/`if` filter that names one spelling makes the script's correctness
irrelevant. Where a spelling cannot be resolved cheaply (a GraphQL mutation
carrying only a node ID), abstain rather than allow, and declare the gap in
writing instead of leaving it for the next red-team pass.

Two corollaries earned the same day:

- **Run the whole suite against an adversarial variant, not just the guards it
  names.** A red-team pass reported a split-literal bypass passing "both guard
  tests"; running the full file showed two behavioural tests going red on it.
  The finding was real but its conclusion was too strong, and only executing it
  told the difference. Later the same pass found a variant that genuinely passed
  all 37, by hiding an identity in a fallback the test harness never reached —
  so the discipline cuts both ways.
- **Say what the tests actually promise.** This ticket claimed a "rampart" twice
  — first for source-literal guards, then for behavioural ones — and was wrong
  both times. No finite set of source checks catches an arbitrarily obfuscated
  reintroduction. The honest sentence is smaller: the tests cover the resolution
  paths the code has, and what protects a short script is that someone reads it.
  Chasing a third variant is the wrong move; correcting the claim is the right
  one.

Related: [[a-test-green-for-an-accidental-reason]], [[measure-whether-a-guard-ever-fired]],
[[verify-each-before-batch-action]].
