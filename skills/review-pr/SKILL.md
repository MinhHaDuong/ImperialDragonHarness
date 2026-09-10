---
name: review-pr
description: "Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation."
disable-model-invocation: false
user-invocable: true
argument-hint: "[pr-number] [worktree=<path>] (defaults to the current branch's open merge request)"
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
below the coder tier (`rules/workflow.md` § Delegation), and an
unpinned Agent inherits the session model, so on a top-tier session this fan-out
silently becomes a top-model wave.

**Concurrency contract (`rules/authoring-skills.md`): parallel-background,
collected by polling.** This skill runs as a `context: fork` (see frontmatter),
and a fork's turn ends the instant it stops calling tools. Delegated subagents
always run in the background and notify the **session**, not this fork. No
launch parameter changes that — there is no foreground option to pass, and a
contract that names one describes a lever that does not exist. The fork stays
alive only by continuing to call tools.

Left alone, the failure is silent and total: the fork ends its turn at the
launch, the completions re-invoke the main loop, no synthesis runs, and no
review is ever posted — while the fork's last message reads like a fan-out in
progress. Observed twice on one merge request, 2026-09-10: ten reviewers
returned real verdicts, two of them `request-changes`, and the merge request
carried nothing.

So the panel is collected from **artifacts**, never from return values:

1. Before launching, write the roster to `<panel>/manifest.txt`, one perspective
   per line. This is the set collection checks against. Without it, "no more
   reports are arriving" cannot be told from "none were ever launched".
2. Each reviewer writes its report to `<panel>/<perspective>.md.part`, then
   renames it to `<panel>/<perspective>.md`. The rename is the completion
   signal: a half-written file never carries the final name.
3. The fork then waits in a single bounded loop until every manifest entry has
   its report or the deadline passes. That wait is what keeps the fork's turn
   alive — the mechanism the absent launch parameter was reaching for.

`<panel>` is `<worktree>/.panel/<pr-number>/` — inside the worktree, never a
temporary directory. Collection assumes launcher and reviewers share a
filesystem, which holds while subagents run on this machine; a container's
temporary directory may be neither shared nor durable. If reviewers ever run in
separate containers, the shared medium has to become the forge itself (each
reviewer posting its own comment, the launcher synthesizing from them) — that
inverts the outage behaviour below, so it is a trade to decide, not to assume.

A perspective still missing at the deadline is **missing, not clear**. Name it
in the posted review and leave it unresolved for the next round.

## Setup

1. **Read the issue** linked to the PR. Note the exit criteria.
2. **Read the diff** of the merge request.
3. **Assess risk level** and determine proportional depth (see table below).
4. **Write the manifest, then launch the review agents** in parallel, in one
   message, per the concurrency contract above. Each agent's prompt must name
   the exact `<panel>/<perspective>.md` path it writes and the `.part`-then-
   rename discipline; an agent that only *returns* its findings has reported to
   a fork that is already gone. On round ≥ 2, scope the set per § Round scoping
   below before launching, and let the manifest list exactly that scoped set:

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

**If the review history cannot be read, stop.** An unreachable forge makes the
round unknown, and both guesses are wrong in their own direction: assuming
round 1 re-runs a full panel over settled ground, assuming higher silently
scopes perspectives out that never cleared. Report that the round could not be
derived and why. Abstaining is the correct verdict when the input is missing.

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
which model runs them (`rules/claude-code.md` § Subagent levers and
`rules/workflow.md` § Delegation).

## Each agent runs

1. Read the issue exit criteria and the diff.
2. Evaluate from its assigned perspective.
3. Report **confidence** (high / medium / low) per finding.
4. Decide a verdict: **approve**, **comment**, or **request-changes**.
5. Write findings and verdict to `<panel>/<perspective>.md.part`, then rename to
   `<panel>/<perspective>.md`. Returning them is not enough and is not the
   contract — the fork that would have read the return value has ended.

## Collection

Sequential-blocking, and bounded. Wait in one loop until every manifest entry
has its report or the deadline passes; give the panel roughly ten minutes.

Then compare what landed against `<panel>/manifest.txt` and classify each
perspective as **reported** or **no report**. This comparison is the check, and
it is the reason the manifest is written before launching: a collection step
that merely gathers whatever files exist returns the same empty-handed success
whether five reviewers approved in silence or none of them ever started.

Never wait unbounded, and never extend the deadline to avoid recording a gap.
Proceed to synthesis with what landed, carrying the gap forward by name.

## Synthesis

1. **Preserve dissent** — surface contradictions verbatim. The human author decides.
2. **Triage by confidence** — investigate low-confidence findings before posting.
3. **Deduplicate** findings across agents.
4. **Run tests**: `make check`
5. **Write the synthesis to `<panel>/review.md` before posting it.** Findings then
   survive a forge outage, a fork that dies mid-step, and a failed post. A review
   that exists only inside a tool call's arguments is gone the moment that call
   fails.
6. **Post a single review** on the merge request, attributing each finding to its
   perspective.
7. **Verify it landed.** Count the reviews on the merge request before posting and
   again after; the count must increase. If it did not, the round did not happen:
   say so, name `<panel>/review.md` so the work is recoverable, and return
   failure. Never report a round complete on the strength of having *called* the
   post — returning a plausible summary while the merge request stayed empty is
   this skill's recorded failure mode, not a hypothetical one (memory
   `verify-fork-under-execution`).
8. **Close with a verdict roster** — one line per perspective in the manifest,
   giving its verdict (approve / comment / request-changes), including the
   perspectives that returned **approve** with nothing to say, and **no report**
   for any that did not land. The next round scopes itself from this roster
   (§ Round scoping): a `no report` perspective is unresolved and re-runs, exactly
   like a `comment`. Silence must never scope a perspective out — a reviewer that
   crashed and a reviewer that approved are opposite outcomes and cannot share a
   spelling. Dedup (step 3) merges *findings*, never verdicts: a perspective whose
   only finding was deduped into another's still records its own comment verdict.

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
