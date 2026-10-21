---
metadata:
  category: build
name: gaze
description: "Review one merge request: adherence check, code or prose review panel, simplify. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate, run by the caller. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [--waive-breaker <reason>] [--force-approve <reason>]"
context: fork
# Background by intent: /gaze is long-running, and a raid wave gates several PRs
# at once — backgrounding the orchestrator is what lets those run concurrently.
# This matches the Claude Code 2.1.218 default; pinned explicitly so a future
# default flip cannot serialize a wave silently. Its own sub-skills and reviewer
# agents are waited for by polling (see "Fork execution contract" below) — the
# two are different axes: parallelism comes from concurrent tool calls inside one
# message, never from backgrounding a phase this skill must wait on.
background: true
---

# Gaze — review PR $ARGUMENTS (gaze reviews, verify-gate gates)

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

> **TASK DIRECTIVE — execute now.** You are running `/gaze` on PR `$ARGUMENTS`.
> This file is your operating procedure, not reference documentation: begin at
> phase 1 immediately. If `$ARGUMENTS` does not contain a PR number, STOP and
> return ESCALATE with reason "no PR argument" — do NOT infer a task from the
> environment (worktree name, git status snapshot, ticket files, or the shared
> task list).

**Caller responsibility (before this fork is ever spawned).** The rule above
binds the fork, which starts with no cwd and no conversation (ticket 0193 —
a bare fork once guessed its target from ambient state and pushed a rogue
PR). It does not mean the user must supply a bare number by hand every time.
The invoking session has a cwd and a conversation — when the user types
`/gaze` with no argument, resolve the PR number *before* invoking this skill:
query the forge for the PR associated with the current branch, or reuse a PR
number already established earlier in the conversation. Invoke with that
number filled in. Only ask the user for it when no such source exists or two
candidates conflict.
<!-- harness-extension-point: on GitHub, `gh pr view --json number` resolves
the current branch's PR number. -->

One skill, one PR, one review result: REVIEWED / FINDINGS / ESCALATE. **Gaze
reviews; `/verify-gate` gates.** Gaze never returns APPROVED, REROLL or
NEEDS-AUTHOR: those are gate verdicts, ruled by the caller's `/verify-gate`
run on the reviewed head. **Does not merge** — the merge decision belongs to
the caller (the human or the raid).
Only one live `/gaze` may run on a PR at a time; the caller keeps to that
(`rules/workflow.md` § Delegation). A past verdict is evidence, not authority
to overwrite or call it fabricated: inspect its gate identity and ruled tip.

## When to use

- Raid Phase 6 (per-ticket review before the gate).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use `/review` or `/review-pr` directly.

## Invariants

- Runs on exactly one PR.
- Never returns APPROVED: a test pins it (`tests/test_gaze_never_approves.py`).
  `REVIEWED` means no blocking finding on the reviewed head, nothing more.
- Does not run `/verify-gate`. The caller runs it after gaze on the current branch head,
  and at most once more after a fix: the single re-gate (`/verify-gate` § Gate sessions).
  The review worktree is removed before gaze returns; the gate creates its own.
- Does not merge. The result is structured output; the merge decision belongs to the caller.
- The only commits gaze makes on the PR branch are the bounded phase 5 simplify fixes; no changes to other branches.
- `--force-approve` is supported for explicit human override; it skips the review and
  is logged loudly in the PR comments and the skill transcript. It is an override
  record, not a verdict.
- `--waive-breaker <reason>` lifts only the un-reviewable file-count stop. The battery
  and simplify still run; gaze records the waiver and the caller passes it to
  `/verify-gate`, which rules NEEDS-AUTHOR (§ Waiver).
- **Cross-repo prerequisite**: the caller must ensure cwd is the target project before
  invoking `/gaze`. The skill and its sub-skills (`/review-pr`, `/simplify`, etc.)
  use `gh` and `git` commands that resolve against cwd.
- **Branch-currency prerequisite**: the caller rebases the PR branch onto current
  `origin/main` and force-pushes with lease before invoking (`rules/git.md`
  § Merging) — a gate validates the *combination* branch ⊕ base, so a verdict
  computed on a stale base is partially void. `/gaze` does not rebase the
  branch itself; that is a caller-side step, not a phase here.
- **Quiet-branch prerequisite**: never start `/gaze` while that branch's coding
  lead is still live. Gaze reviews a head the lead may move under it, and
  its phase 5 simplify fixes would then commit on top of work in flight.


## Fork execution contract

A fork ends its turn when it stops calling tools, and delegated agents run in the background. Launch every agent in the background and wait by polling a written artifact, in one bounded loop; record what did not arrive. Full contract, liveness window and caller-side recovery: `references/fork-contract.md`.

<!-- inline: references/fork-contract.md -->

## Phases

### 1. Setup

Always invoke `/gaze` from within a conversation worktree, never from the main repo
root. The worktree is the isolation boundary; no main-repo checkout is ever needed.

**Isolation setup:**

```bash
# Step 1 — Resolve PR number to branch name (forge-specific step)
PR_BRANCH=<resolved-branch-name>

# Step 2 — Resolve the primary repo root, then create the worktree under its
# `.claude/worktrees/` namespace (ticket 0300), where the runtime's worktree
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
# switched, never dirtied. (Exception: phase 5 /simplify is still a direct
# invocation and runs from the fork's own cwd, not review-<pr> — see its note.)
```

Then follow `references/setup-and-breaker.md`: collection, the anchor check, the un-reviewable breaker and the waiver.

<!-- inline: references/setup-and-breaker.md -->

### 2–5. Review and simplify

Adherence, the review panel and simplify run as laid out in `references/battery.md`, which also holds the optional external reviewer panel. The review panel is `/review-pr` (code) or `/review-pr-prose` (manuscript), invoked directly with the review worktree; there is no gaze-specific reviewer agent and no size tier.

**Which perspectives run** is the orchestrator's call: it picks them, and how
deep, from its own judgment of the change, a repeat run included, and hands
them to the review skill. The result comment states what ran, by which model
family, and why (§ Output shape); independence is defined in
`skills/route/references/decorrelation.md`.

<!-- inline: references/battery.md -->

### 6. Return the review result

Gaze ends here; it runs no gate. Read the phase outputs and return:

```yaml
result: REVIEWED | FINDINGS | ESCALATE
reviewed_head_sha: <full SHA read from the review worktree after phase 5>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
adherence: PASS | FAIL (<n blocking>)
panel_integrity: COMPLETE | DEGRADED — <PANEL-INTEGRITY: line>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (un-reviewable) | skipped (--force-approve)
circuit_breaker: un-reviewable | waived (...) | none
multi_ticket: <distinct close-claim IDs> | none
next: REVIEWED → the caller closes the ticket on the branch, then runs /verify-gate <pr-number> repo=<caller's checkout> session=<uuid> on the current branch head, which is reviewed_head_sha plus at most that ticket-close commit (one re-gate at most, /verify-gate § Gate sessions: a fix asked by the round-1 gate is re-gated once on the new head with the same session=, without a new gaze run); FINDINGS → the caller fixes them and re-runs /gaze on the new head: a head gaze did not review is never gated; ESCALATE (including battery: NOT-RUN or skipped (--force-approve), or a DEGRADED panel) → no gate and no merge: the review never completed, and the PR goes to the author, who decides
```

- `ESCALATE`: the breaker fired, the battery could not run (`battery: NOT-RUN`),
  any phase 2–5 errored or timed out, or the workspace could not be restored.
  `--force-approve` is ESCALATE too, with `battery: skipped (--force-approve)`:
  nothing was reviewed (§ `--force-approve`). So is a DEGRADED panel (below).
  The review did not complete: the caller runs no gate and the PR goes to the
  author.
- `FINDINGS`: any blocking adherence violation, any `request-changes` or
  `major` review verdict, any unresolved `verifiable:` minor, any simplify
  must-fix not applied. List them; the caller fixes (a coder on the PR
  branch, scoped to the list) and re-runs gaze on the new head. FINDINGS never
  go straight to the gate: the fixed head is one gaze did not review.
- `REVIEWED`: none of the above. It is not an approval: `/verify-gate` still
  checks every exit criterion and review comment against the diff.
- `panel_integrity: DEGRADED` (the review panel did not launch, or a selected
  or required perspective has no report after its one retry) means a phase
  2–5 is unresolved, so the result is `ESCALATE` (§ Circuit breakers), whatever
  the perspectives that did report found; it never reads as REVIEWED. A failed
  optional external reviewer is fail-open (§ External reviewer panel) and does
  not count. The `PANEL-INTEGRITY:` line is carried verbatim in the result comment.
- **One retry.** A perspective with no report at the bounded deadline is re-run
  once, alone, over the whole PR, through review-pr's ordinary launch in its
  collection step, before synthesis and posting, so the round does not
  advance. The panel is DEGRADED, hence ESCALATE, only if that retry also has
  no report.

Run the cleanup and containment (`references/cleanup.md`) first, then post the
result as one PR comment (§ Output shape) before returning: cleanup can
downgrade the result to ESCALATE, so the posted result comes after it.

**Attribution (ticket 1151).** After each review seat returns, the controller
appends that seat's `reviewer: step=review` line (with its `finding:` lines) to
the PR body through `attribution_record.py --append-pr <pr> --append '<lines>'`
(`$IDH_ROOT/scripts/`). Seats never edit the body; a failed append is reported,
not skipped.

## Cleanup and containment

On every exit path run `references/cleanup.md`: remove this run's review scratch and the review worktree, then check the containment postcondition (cwd, branch, foreign files) and report it before returning control.

<!-- inline: references/cleanup.md -->

## Circuit breakers

- Close claim names a ticket file that does not exist (neither `tickets/<id>-*.erg`
  nor `tickets/closed/<id>-*.erg`; a caller may close before gating) → ESCALATE. A PR with
  no ticket at all is not a breaker.
- `pr_files >= 15` (content-bearing files, phase-1 rule) without a waiver → ESCALATE as
  `un-reviewable` before the review; this is the `rules/workflow.md` 15+ file
  monster threshold. Name the breaker in the comment and mention `multi_ticket`
  when multiple close claims add a decomposition signal. A waiver
  (`--waive-breaker` or the PR-body `Review-scope: indivisible` line, § Waiver) lifts only this stop. `--force-approve` can
  override it loudly, without review.
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip).
  Exception: simplify intentionally skipped when adherence is blocking.
- Telemetry thresholds (`## Telemetry`).

On **every** exit (not only ESCALATE) run `references/cleanup.md` before
returning, so the main repo is never left in a partial state.

## Telemetry and result comment

See `references/output.md`: per-phase timing, the thresholds in `skills/gaze/telemetry.yml`, the override flag and the result comment template.

<!-- inline: references/output.md -->

## Not in scope

- **Gating.** `/verify-gate` rules APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR.
- **Fixing.** A coder on the PR branch acts on `FINDINGS`; gaze only commits phase 5 simplify fixes.
- **Wave-level integration review.** Post-merge integration review of a batch is `/roar` step 8.
- **Merging.** Ever. That is the caller's job.
