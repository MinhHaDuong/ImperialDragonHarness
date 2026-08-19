---
name: review-pr
description: "Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation."
disable-model-invocation: false
user-invocable: true
argument-hint: "[pr-number] (defaults to the current branch's open merge request)"
context: fork
# Foreground: /gaze runs this as phase 4 (Agent C) and blocks on its structured
# output. Claude Code 2.1.218 made `context: fork` skills background by default;
# a fork cannot wait on a background completion, so the default would orphan
# this phase — ticket 0250. Standalone use is unaffected.
background: false
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
below the coder tier (rules/workflow.md § "Reviewer decorrelation"), and an
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
   (`run_in_background: false`), per the concurrency contract above. On
   round ≥ 2, scope the set per § Round scoping below before launching:

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

### Round scoping

The table above prices **round 1**. Round 1 always runs the full proportional
panel — no perspective is skipped on a PR's first review.

Derive the round here, from the PR itself: count the reviews already posted by
this skill on the merge request; the round is that count plus one. No caller
passes a round number, and no caller is trusted to have counted — the PR's
review history is the only source.

For round N > 1, re-run only:

- the perspectives whose round N−1 verdict was **comment** or
  **request-changes** — those are the ones with something outstanding; and
- **one regression check**: a single regression agent covering all the perspectives that
  cleared in round N−1, asked only whether the fixes since then broke anything
  those perspectives had approved. One agent for the whole cleared set, not one
  per perspective — it is a cheap sanity pass, not a re-review.

A perspective that returned **approve** in round N−1 does not run again on its
own; the regression check stands in for it.

**Reset exception.** If the diff since the last review touches files that were
not in it, or changes more than roughly half of its lines, the fixes are a
rewrite rather than a patch — the cleared perspectives cleared different code.
Run the full proportional panel for this round — scoping is ignored. The
derived round number itself is untouched: the count of posted reviews cannot
be rolled back, and the review this round posts still increments it.

Model pins are unaffected: scoping changes *which* perspectives run, never
which model runs them (`rules/workflow.md` § Subagents, reviewer
decorrelation).

This is not gaze's **Convergence mode** (ticket 0315, default off) under
another name. Round scoping works *within* one review invocation, across its
rounds, and always runs at least the objecting perspectives plus the
regression check. Convergence mode works at the *caller* level, deciding
whether a whole repeat `/gaze` runs its panel again at all. The two are
orthogonal; neither replaces the other, and enabling or disabling one says
nothing about the other.

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
6. **Close with a verdict roster** — one line per perspective that ran, giving
   its verdict (approve / comment / request-changes), including the
   perspectives that returned **approve** with nothing to say. The next round
   scopes itself from this roster (§ Round scoping), so a perspective missing
   from it reads as cleared. Dedup (step 3) merges *findings*, never verdicts:
   a perspective whose only finding was deduped into another's still records
   its own comment verdict.

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
