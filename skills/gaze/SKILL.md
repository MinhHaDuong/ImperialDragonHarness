---
metadata:
  category: build
name: gaze
description: "Review one merge request by intention: the caller says what to verify and why; gaze plans the method, runs it once, checks the plan against what ran and records one result. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [verify <what> because <why>]"
context: fork
# Background by intent: /gaze is long-running, and a raid wave gates several PRs
# at once — backgrounding the orchestrator is what lets those run concurrently.
# This matches the runtime default; pinned explicitly so a future
# default flip cannot serialize a wave silently. Its own sub-skills and reviewer
# agents are waited for by polling (see "Fork execution contract" below) — the
# two are different axes: parallelism comes from concurrent tool calls inside one
# message, never from backgrounding a phase this skill must wait on.
background: true
---

# Gaze — review by intention: $ARGUMENTS (gaze reviews, verify-gate gates)

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

> **TASK DIRECTIVE — execute now.** You are running `/gaze` with `$ARGUMENTS`:
> a PR number, then an optional intent. This file is your operating procedure,
> not reference documentation: begin at phase 1 immediately. If `$ARGUMENTS`
> does not start with a PR number, STOP and
> return ESCALATE with reason "no PR argument" — do NOT infer a task from the
> environment (worktree name, git status snapshot, ticket files, or the shared
> task list).

One skill, one PR, one pass, one review result: REVIEWED / FINDINGS /
ESCALATE. **Gaze reviews; `/verify-gate` gates.** Gaze never returns APPROVED,
REROLL or NEEDS-AUTHOR: those are gate verdicts, ruled by `/verify-gate`.
**Does not merge.** Input precondition: no other live `/gaze` on the PR
(`rules/workflow.md` § Delegation). A past verdict is evidence, not authority
to overwrite or call it fabricated: inspect its gate identity and ruled tip.

**Intent.** Free text after the PR number, in the shape
`/gaze <pr> verify <what> because <why>`; the parsing is lenient and nothing
is refused for its wording. The what bounds the scope, the why sets the risk.
With no intent, the what is the whole merge request against its ticket's exit
criteria. A later round is a new, narrower intent ("verify the fixes for
findings 1 and 3"), not a re-run of the whole review.

Trust: the caller trusts gaze's plan; gaze trusts the coder's tests and the
gate's checks. Verify: phase 4, and the result shows the intent beside the
plan. Monitor: trace-doctor and the gaze telemetry judge plan sizing across
runs.

## When to use

- Raid Phase 6 (per-ticket review before the gate).
- Any time a caller wants a stated question about one PR settled before the gate.
- **Do NOT** use for quick sanity — use the native `/review` directly.

## Invariants

- Runs on exactly one PR.
- Never returns APPROVED: a test pins it (`tests/test_gaze_never_approves.py`).
  `REVIEWED` means no blocking finding on the reviewed head, nothing more.
- Does not run `/verify-gate`.
  The review worktree is removed before gaze returns; the gate creates its own.
- Does not merge. The result is structured output.
- **One pass, no recursion.** The pass may run several workers in parallel,
  as the plan says, but no worker launches a further review, gaze does not
  review its own findings again, and there is no internal round or fix loop.
  Findings go back to the caller.
- **Read-only on the code.** Gaze makes no commits and no pushes, on the PR
  branch or any other, and writes nothing in the caller's worktree; simplify
  findings are reported like any other and the coder acts on them. Checks run
  in gaze's own review worktree, removed with its scratch before returning
  (§ Cleanup and containment).
- **No mechanical adherence.** The `-m adherence` tests and verify-adherence's
  mechanical tier belong to the merge gate's record (`pytest-guard`) and to
  hunt's self-gate. Judging the change against the written rules is review: a
  perspective the plan may choose.
- **Cross-repo prerequisite**: the caller starts `/gaze` inside the target project.
  The cwd names the repository and nothing else: branch, head and files come
  from the PR number, reviewed in gaze's own `review-<pr>` worktree.
- **Branch-currency prerequisite**: the caller rebases the PR branch onto current
  `origin/main` and force-pushes with lease before invoking (`rules/git.md`
  § Merging) — a gate validates the *combination* branch ⊕ base, so a verdict
  computed on a stale base is partially void. `/gaze` does not rebase the
  branch itself; that is a caller-side step, not a phase here.
- **Quiet-branch prerequisite**: never start `/gaze` while that branch's coding
  lead is still live. Gaze reviews a head the lead may move under it, and
  its findings would then describe a head that is already gone.


## Fork execution contract

A fork ends its turn when it stops calling tools, and delegated agents run in the background. Launch every agent in the background and wait by polling a written artifact, in one bounded loop; record what did not arrive. Full contract: `references/fork-contract.md`.

<!-- inline: references/fork-contract.md -->

## Phases

### 1. Setup

First, start the duration clock (`references/output.md` § Duration clock).

Always invoke `/gaze` from within a conversation worktree, never from the main repo
root. The worktree is the isolation boundary; no main-repo checkout is ever needed.

**Isolation setup:**

```bash
# Step 1 — Resolve PR number to branch name (forge-specific step)
PR_BRANCH=<resolved-branch-name>

# Step 2 — Resolve the primary repo root, then create the worktree under its
# `.claude/worktrees/` namespace, where the runtime's worktree
# isolation covers it like every other worktree; never under /tmp.
primary_root=$(git rev-parse --show-toplevel)
primary_root="${primary_root%%/.claude/worktrees/*}"   # strip if we run from a session worktree
review_tree="$primary_root/.claude/worktrees/review-<pr-number>"
git fetch origin "$PR_BRANCH" || exit 1
if ! git worktree add "$review_tree" origin/"$PR_BRANCH" || ! test -d "$review_tree"; then
    echo "gaze: cannot create isolated review worktree for PR <pr-number>; refusing to fall back into the invoking tree" >&2
    exit 1
fi
# The reviewer agents (review worktree via git -C) run inside
# $primary_root/.claude/worktrees/review-<pr-number>; the main repo is never
# switched, never dirtied.
```

Then follow `references/setup-and-breaker.md`: collection, the anchor check and the close-claim check.

<!-- inline: references/setup-and-breaker.md -->

### 2. Plan

Before launching anything, write the plan: method, items (each worker or
check, with its model and family), budget. Derive it from the intent and from
the change's nature, size, location and history. The guidance, with worked
cases, is `references/plan.md`; the plan file is `<panel>/manifest.txt`.

<!-- inline: references/plan.md -->

### 3. Execute

Exactly the plan, nothing added: launch its seats and checks and collect
their reports (`references/panel.md`; on prose also
`references/prose-panel.md`).
Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line").

<!-- inline: references/panel.md -->

<!-- inline: references/prose-panel.md -->

### 4. Verify

Compare the plan with what was done:
`python3 "$IDH_ROOT/scripts/seat_clock.py" plan-check <panel>`. It fails when a
planned item has no report, and names as deviations a worker of another
family than planned (from the worker's own first line) and an item over the
budget. Gaze adds what the script cannot see: whether the run covered the
stated what, and the reason for each deviation. There is no retry: a worker
that timed out or could not be reached is a deviation the caller decides on.

- `ESCALATE`: `plan check: FAIL` with no substitute that still settles the
  what, a circuit breaker fired, or the workspace could not be restored. The
  review did not complete.
- `FINDINGS`: any `blocking` seat verdict, any unresolved `verifiable:` minor,
  any simplify must-fix. List them.
- `REVIEWED`: none of the above, the what covered. It is not an approval:
  `/verify-gate` still checks every exit criterion and review comment against
  the diff.

### 5. Record

Run the cleanup and containment (`references/cleanup.md`) first, since it can
downgrade the result to ESCALATE, then post the result as one PR comment
(§ Output shape) and return the same text:

```yaml
result: REVIEWED | FINDINGS | ESCALATE
reviewed_head_sha: <full SHA read from the review worktree after the pass>
intent: <verbatim | default>
plan check: PASS | PASS with deviations — <...> | FAIL — <...>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
```

**Attribution.** After each seat returns, the controller appends that seat's
`reviewer: step=review` line (with its `finding:` lines) to the PR body
through `attribution_record.py --append-pr <pr> --append '<lines>'`
(`$IDH_ROOT/scripts/`): the register of who reviewed, beside the result
comment, the register of what was found. Seats never edit the body; a failed
append is reported, not skipped.

## Cleanup and containment

On every exit path run `references/cleanup.md`: remove this run's review scratch and the review worktree, then check the containment postcondition (cwd, branch, foreign files) and report it before returning control.

<!-- inline: references/cleanup.md -->

## Circuit breakers

- Close claim names a ticket file that does not exist (neither `tickets/<id>-*.erg`
  nor `tickets/closed/<id>-*.erg`; the ticket may already be closed on the branch) → ESCALATE. A PR with
  no ticket at all is not a breaker.
- `plan check: FAIL` without a substitute that settles the what → ESCALATE
  (phase 4).
- Telemetry thresholds (`## Telemetry`).

On **every** exit (not only ESCALATE) run `references/cleanup.md` before
returning, so the main repo is never left in a partial state.

## Telemetry and result comment

See `references/output.md`: per-phase timing, the thresholds in `skills/gaze/telemetry.yml` and the result comment template.

<!-- inline: references/output.md -->

## Not in scope

- **Gating.** `/verify-gate` rules APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR.
- **Fixing.** Gaze makes no commits; it fixes no finding, simplify's included.
- **Mechanical adherence.** The merge gate's record runs it.
- **Wave-level integration review.** Post-merge integration review of a batch is `/roar` step 8.
- **Merging.** Ever.
