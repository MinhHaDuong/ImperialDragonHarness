---
metadata:
  category: build
name: gaze
description: "Review one merge request: plan the checks that settle what the caller asks, run them once, compare the plan with what ran, post one result. Returns REVIEWED / FINDINGS / ESCALATE, never APPROVED. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [verify <what> because <why>]"
context: fork
# Background: gaze is long-running; its own workers are waited for by polling
# (Fork execution contract below), never by backgrounding a phase it must wait on.
background: true
---

# Gaze — review merge request $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

**Input.** A PR number, then optional free text saying what to verify and
why (`verify <what> because <why>`), read leniently. With none, the what is the
whole merge request against its ticket's exit criteria. Without a PR number,
return ESCALATE with reason "no PR argument".

## Invariants

- **One pass, no recursion.** One PR. The pass may run several workers in
  parallel; no worker launches a further review, gaze does not review its own
  findings again, and there is no internal round or fix loop.
- **Read-only on the code.** Gaze makes no commits, no pushes, and writes nothing in the
  caller's worktree. Checks run in gaze's own `review-<pr>` worktree, removed
  with its scratch before returning (§ Cleanup and containment).
- No mechanical adherence: the `-m adherence` tests are not gaze's to run.
  Judging the change against the written rules is review, and the plan may
  choose it.
- Never returns APPROVED (pinned by `tests/test_gaze_never_approves.py`).
  REVIEWED means no blocking finding on the reviewed head, nothing more.
- Does not merge.
- No other live `/gaze` on the same PR.
- Started inside the target project; branch, head and files come from the PR
  number.

## Fork execution contract

A fork ends its turn when it stops calling tools, and delegated agents run in the background. Launch every agent in the background and wait by polling a written artifact, in one bounded loop; record what did not arrive. Full contract: `references/fork-contract.md`.

<!-- inline: references/fork-contract.md -->

## Phases

### 1. Setup

Start the duration clock (`references/output.md` § Duration clock), then
create the review worktree.

**Isolation setup:**

```bash
PR_BRANCH=<resolved-branch-name>   # forge-specific: PR number to branch
primary_root=$(git rev-parse --show-toplevel)
primary_root="${primary_root%%/.claude/worktrees/*}"   # strip if run from a session worktree
review_tree="$primary_root/.claude/worktrees/review-<pr-number>"
git fetch origin "$PR_BRANCH" || exit 1
if ! git worktree add "$review_tree" origin/"$PR_BRANCH" || ! test -d "$review_tree"; then
    echo "gaze: cannot create isolated review worktree for PR <pr-number>; refusing to fall back into the invoking tree" >&2
    exit 1
fi
```

Then `references/setup-and-breaker.md`: collection, the anchor check and the
close-claim check.

<!-- inline: references/setup-and-breaker.md -->

### 2. Plan

Before launching anything, write the plan to `<panel>/manifest.txt`: method,
items (each worker or check, with its model and family), budget. Guidance and
worked cases: `references/plan.md`.

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
  what, a circuit breaker fired, or the workspace could not be restored.
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
plan check: PASS | PASS with deviations — <...> | FAIL — <...>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
```

**Attribution.** After each seat returns, append its `reviewer: step=review`
line, with its `finding:` lines, to the PR body through
`python3 "$IDH_ROOT/scripts/attribution_record.py" --append-pr <pr> --append '<lines>'`.
Seats never edit the body; a failed append is reported, not skipped.

## Cleanup and containment

On every exit path run `references/cleanup.md`: remove this run's review scratch and the review worktree, then check the containment postcondition (cwd, branch, foreign files) and report it before returning.

<!-- inline: references/cleanup.md -->

## Circuit breakers

- The close claim names a ticket file that exists neither under `tickets/`
  nor `tickets/closed/` → ESCALATE. A PR with no ticket is not a breaker.
- The phase 4 ESCALATE conditions.
- Telemetry thresholds (`references/output.md`).

## Telemetry

Per-phase timing and the thresholds in `skills/gaze/telemetry.yml`: `references/output.md`.

<!-- inline: references/output.md -->
