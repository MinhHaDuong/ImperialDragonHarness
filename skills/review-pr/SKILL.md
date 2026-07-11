---
name: review-pr
description: Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation.
disable-model-invocation: false
user-invocable: true
argument-hint: [pr-number] (defaults to the current branch's open merge request)
context: fork
---

# Review PR $ARGUMENTS — multi-perspective agent review

> **TASK DIRECTIVE — execute now.** You are running `/review-pr` on PR
> `$ARGUMENTS` (a PR number, optionally followed by `worktree=<path>`). This
> file is your operating procedure, not reference documentation: start the
> setup immediately. If `worktree=<path>` is present, `cd` into that path
> before any git or forge command — forked sub-skills do not inherit the caller's
> cwd. If `$ARGUMENTS` does not contain a PR number, do NOT infer a task
> from the environment (worktree name, git status snapshot, ticket files, or
> the shared task list) — resolve the missing *argument* from the forge
> instead: query the forge CLI for the open merge request attached to the
> current branch; if exactly one exists, announce "reviewing PR #N (<title>)
> — resolved from branch <branch>" and proceed. If that yields nothing or
> several, list the actual open merge requests and STOP so the user can pick
> from real candidates. Never suggest a fabricated example number — an
> invented "e.g. #N" anchors the user into re-invoking on the wrong PR
> (2026-06-10: exactly that burned a five-agent panel on an already-merged
> PR while the intended target sat unreviewed).

Spin multiple agents in parallel, each with a distinct perspective. Run all
agents in fresh contexts, each pinned to **`model: sonnet`** — reviewers stay
below the coder tier (rules/workflow.md § "Sonnet reviews Opus's work"), and an
unpinned Agent inherits the session model, so on a top-tier session this fan-out
silently becomes a top-model wave.

**Concurrency contract (rules/workflow.md § "Concurrency discipline"):
parallel-FOREGROUND.** This skill runs as a `context: fork` (see frontmatter),
and a fork's turn ends the instant it stops calling tools. Launch the panel in
**one message** as **foreground** Agent calls (`run_in_background: false`) so
the fork blocks until every reviewer returns, then synthesizes. Never launch
them in the background: a fork cannot wait on background agents — it ends its
turn at the launch, the completions re-invoke the MAIN loop, and no synthesis
runs and no review is ever posted.

## Setup

1. **Read the issue** linked to the PR. Note the exit criteria.
2. **Read the diff** of the merge request.
3. **Assess risk level** and determine proportional depth (see table below).
4. **Launch review agents** in parallel — **foreground**
   (`run_in_background: false`), all in one message, per the concurrency
   contract above; the fork must block on the panel, never end its turn with
   reviewers in flight:

| Agent | Focus | Key question |
|---|---|---|
| **Correctness** | Logic, edge cases, test coverage | Does this do what the exit criteria say? |
| **Consistency** | Style, naming, docs, stale references | Does this fit the rest of the codebase? |
| **Scope** | Over-engineering, unrelated changes | Does this change *only* what the ticket asks? |
| **Red team** | Adversarial inputs, broken invariants | How can this break? |
| **Doc propagation** | Downstream text accuracy | Do docs and configs still match the code? |

### Proportional depth

| PR risk | Agents |
|---|---|
| Trivial + user present | **Skip PR** — merge directly |
| Trivial (typo, config) | Correctness only |
| Standard | Correctness + Consistency |
| Standard + scripts | + Doc propagation |
| Substantial | All five |
| High-risk (schema, methodology) | All five + domain experts |

## Each agent runs

1. Read the issue exit criteria and the diff.
2. Evaluate from its assigned perspective.
3. Report **confidence** (high / medium / low) per finding.
4. Return verdict: **approve**, **comment**, or **request-changes**.

## Synthesis

1. **Preserve dissent** — surface contradictions verbatim. The human author decides.
2. **Triage by confidence** — investigate low-confidence findings before posting.
3. **Deduplicate** findings across agents.
4. **Run tests**: `make check`
5. **Post a single review** on the merge request, attributing each finding to its perspective.

## Minor finding tags (mandatory)

Every non-blocker finding posted in the review carries exactly one prefix:

| Prefix | Meaning |
|---|---|
| `verifiable:` | A current failing assertion is attached (test_id, command output, or commit SHA:file:line). The claim is reproducible now. |
| `consider:` | Hypothesis worth flagging, no enforcement. No test exists and none is required. Author may dismiss. |
| `nofollow:` | Intentionally not pursued (out of scope, duplicate, stylistic preference). Recorded for the audit trail; no action expected. |

Rules:
- Ambiguous "this might break X" / "could cause Y" language is forbidden. Either produce the failing assertion (`verifiable:`) or downgrade to `consider:`.
- A `verifiable:` finding without attached evidence is a posting bug — hold the review until the evidence exists or retag.
- Blockers (`request-changes`) are not tagged; tags are for the minor/comment tier only.
- The tag set is shared with `/review-pr-prose` and `/verify-gate`. Keep all three in sync. Evidence forms differ by domain: code reviews use test_id/SHA:file:line; prose reviews use line citations and numeric rechecks.

## Code-quality escalation

| Severity | Action |
|---|---|
| Blocks correctness (bug, data loss) | request-changes |
| Introduced by this PR | request-changes |
| Pre-existing but touched | comment + new ticket |
| Pre-existing and untouched | investigate → ticket if warranted |
