---
metadata:
  category: build
name: gaze
description: "Review one merge request: plan the checks that settle what the caller asks, run them once, check the plan against what ran, post one result: REVIEWED / FINDINGS / ESCALATE, never APPROVED."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [verify <what> because <why>]"
context: fork
# Background: gaze is long-running; its own workers are waited for by polling
# (Fork execution contract below), never by backgrounding a phase it must wait on.
background: true
---

# Gaze — review merge request $ARGUMENTS

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

**Input.** A PR number, then optional free text saying what to verify and
why (`verify <what> because <why>`), read leniently. With none, the what is the
whole merge request against its ticket's exit criteria. Without a PR number,
return ESCALATE with reason "no PR argument".

## Invariants

- **One pass, no recursion.** One PR. The pass may run several workers in
  parallel; no worker launches a further review, and there is no second pass
  or fix loop. Within the pass, gaze checks each finding before reporting it
  (reproduces it or reads the code it cites) and drops what does not hold.
- **Read-only on the code.** Gaze makes no commits and no pushes, and writes
  nothing in the caller's worktree. It writes only its report: the result
  comment and its attribution lines on the PR, and the same text returned to
  the caller. Checks run in gaze's own review worktree, removed with its
  scratch before returning (§ Cleanup and containment).
- Never returns APPROVED (pinned by `tests/test_gaze_never_approves.py`).
  REVIEWED means no blocking finding on the reviewed head, nothing more.
- Does not merge.
- **15 minutes, then deliver.** The pass has a hard 15-minute deadline from
  its start (`skills/gaze/telemetry.yml`). At the deadline gaze stops waiting
  and delivers what it has, finished or not. A change that cannot be verified
  in 15 minutes is itself the signal.
- **One live gaze per PR.** The review worktree `review-<pr-number>` is the
  lock (§ 1. Setup).
- Started inside the target project; branch, head and files come from the PR
  number.

## Fork execution contract

A fork ends its turn when it stops calling tools, and delegated agents run in the background. Launch every agent in the background and wait by polling a written artifact, in one bounded loop; record what did not arrive. Full contract: `references/fork-contract.md`.

<!-- inline: references/fork-contract.md -->

## Phases

### 1. Setup

One call does the whole phase (clock, isolation worktree, anchor check, PR
state, ticket files, panel directory):

```bash
python3 "$IDH_ROOT/scripts/gaze_setup.py" <pr-number>
```

It prints one `key=value` block (`clock`, `branch`, `head`, `ci`,
`review_tree`, `panel`, `ticket`, the changed-file roster; PR body and
comments are written to files in the panel directory). Keep `clock` and
`branch` literally for § 5. Exit 1 blocks (conflicts, a close claim naming a
nonexistent ticket file, no isolated worktree: never fall back into the
invoking tree), 2 is a read or anchor failure, 3 means another gaze is live on
this PR (`review-<pr-number>` is the lock; liveness window
`fork_liveness_seconds`, `skills/gaze/telemetry.yml`): return ESCALATE
"another gaze is live on this PR". A dead run's leftover tree is cleaned by
the script. Details and what stays judgment: `references/setup-and-breaker.md`.

<!-- inline: references/setup-and-breaker.md -->

### 2. Plan

Before launching anything, write the review plan to `<panel>/manifest.txt`,
where `<panel>` is `$review_tree/.panel/<pr-number>/`: method, items (each
worker or check, with its model and family), budget. Work gaze does itself is
an item like any other, worker `self`, and writes its own report to
`<panel>/<item>.md`, opening with the same `worker:` line every report
carries. Guidance and worked cases: `references/plan.md`.

<!-- inline: references/plan.md -->

### 3. Execute

Run exactly the plan: launch its seats and checks and collect their reports
(`references/panel.md`; on prose also `references/prose-panel.md`).
Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line").

<!-- inline: references/panel.md -->

<!-- inline: references/prose-panel.md -->

### 4. Verify

Compare the plan with what was done:
`python3 "$IDH_ROOT/scripts/seat_clock.py" plan-check <panel>`. It fails when a
planned item has no report (an empty one, or a worker's without its `worker:`
first line, counts as none), and names as deviations a worker of another
family than planned and an item over budget. Add what the script cannot see:
whether the run covered the stated what, and the reason for each deviation.
No retry: a worker that timed out or could not be reached is a deviation.

- `ESCALATE`: `plan check: FAIL` with no substitute that still settles the
  what, a circuit breaker fired, the workspace could not be restored, or the
  deadline passed with items not finished and no blocking finding in hand
  (reason: "not verifiable within 15 minutes").
- `FINDINGS`: any `blocking` seat verdict, any unresolved `verifiable:` minor,
  any simplify must-fix.
- `REVIEWED`: none of the above, and the what covered.

### 5. Output

Run the cleanup (`references/cleanup.md`) first, since it can downgrade the
result to ESCALATE. Then post one PR comment and return the same text; its
full template is `references/output.md`:

```yaml
result: REVIEWED | FINDINGS | ESCALATE
reviewed_head_sha: <full SHA read from the review worktree after the pass>
intent: <verbatim | default>
review plan: <method; items as name (model, family); budget>
plan check: PASS | PASS with deviations — <...> | FAIL — <...>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
```

**Attribution.** As each seat returns, collect its `reviewer: step=review`
line, with its `finding:` lines, in a file; `gaze_close.py --attribution-file`
appends them to the PR body through `attribution_record.py --append-pr`.
Seats never edit the body; a failed append is reported, not skipped.

## Cleanup and containment

On every exit path run `references/cleanup.md` through the one closing call
(`python3 "$IDH_ROOT/scripts/gaze_close.py" <pr> --branch <branch> --token <clock> --attribution-file <file> --comment-file <file>`;
the attribution file is required, empty when no seat ran):
it appends attribution first, then removes this run's review scratch and the review worktree, checks the
containment postcondition (cwd, branch, foreign files)
and posts the comment. On a blocked cleanup (exit 1) attribution is already
appended, the script posts nothing, and the calling gaze posts the ESCALATE
comment itself.

<!-- inline: references/cleanup.md -->

## Circuit breakers

- The close claim names a ticket file that exists neither under `tickets/`
  nor `tickets/closed/` → ESCALATE. A PR with no ticket is not a breaker.
- The phase 4 ESCALATE conditions.
- Telemetry thresholds (`references/output.md`).

## Telemetry

Per-phase timing and the thresholds in `skills/gaze/telemetry.yml`: `references/output.md`.

<!-- inline: references/output.md -->
