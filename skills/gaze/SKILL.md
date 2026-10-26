---
metadata:
  category: build
name: gaze
description: "Review one merge request: adherence check, code or prose review panel, simplify. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [--brief 'seats=<a,b|none>; scope=<all|A..B|paths:p,q>; why=<text>'] [--force-approve <reason>]"
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

# Gaze — review PR $ARGUMENTS (gaze reviews, verify-gate gates)

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

> **TASK DIRECTIVE — execute now.** You are running `/gaze` on PR `$ARGUMENTS`.
> This file is your operating procedure, not reference documentation: begin at
> phase 1 immediately. A `--brief '<...>'` in `$ARGUMENTS` is the caller's
> brief (§ The brief). If `$ARGUMENTS` does not contain a PR number, STOP and
> return ESCALATE with reason "no PR argument" — do NOT infer a task from the
> environment (worktree name, git status snapshot, ticket files, or the shared
> task list).

One skill, one PR, one review result: REVIEWED / FINDINGS / ESCALATE. **Gaze
reviews; `/verify-gate` gates.** Gaze never returns APPROVED, REROLL or
NEEDS-AUTHOR: those are gate verdicts, ruled by `/verify-gate`. **Does not
merge.** Input precondition: no other live `/gaze` on the PR
(`rules/workflow.md` § Delegation). A past verdict is evidence, not authority
to overwrite or call it fabricated: inspect its gate identity and ruled tip.

## When to use

- Raid Phase 6 (per-ticket review before the gate).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use the native `/review` directly.

## Invariants

- Runs on exactly one PR.
- Never returns APPROVED: a test pins it (`tests/test_gaze_never_approves.py`).
  `REVIEWED` means no blocking finding on the reviewed head, nothing more.
- Does not run `/verify-gate`.
  The review worktree is removed before gaze returns; the gate creates its own.
- Does not merge. The result is structured output.
- Gaze makes no commits, on the PR branch or any other: simplify findings are reported like panel findings and the coder acts on them.
- `--force-approve` is supported for explicit human override; it skips the review and
  is logged loudly in the PR comments and the skill transcript. It is an override
  record, not a verdict.
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

Then follow `references/setup-and-breaker.md`: collection, the anchor check and the close-claim preflight.

### The brief

The caller decides how much review the change gets; gaze runs that decision.
The brief names the perspectives (seats) and the scope:
`seats=<a,b|none>; scope=<all|A..B|paths:p,q>; why=<text>`. Seat names are
the code perspectives (`correctness`, `consistency`, `scope`, `red-team`,
`doc-propagation`), the prose seats (`referee`, `venue-expert`, `ai-tells`,
`editorial-brief`), `simplify` (phase 5) and `external` (the optional
external panel); `seats=none` runs mechanical adherence only. Adherence
(Agent A) runs on every brief. How to size a brief is the orchestrator's
judgement, guided in one place: `skills/route/references/decorrelation.md`
§ Scale the review to the risk.

Resolve it in the review worktree before launching anything:

```bash
cd "$review_tree" && python3 "$IDH_ROOT/scripts/gaze_brief.py" resolve --brief '<brief, empty when none>' --base origin/<base> --head HEAD
```

- **Exit 2: refused.** An unknown seat, a key gaze does not know, a range or
  path outside the diff: gaze launches nothing, cleans up and returns
  ESCALATE with the printed `brief: refused — <reason>` line in the result
  comment. It never widens or narrows a brief to make it fit.
- **Exit 0: run exactly that.** `panel_seats:` is the panel roster: the
  manifest lists those perspectives and no other, checked by
  `panel-manifest-check.py <manifest> --seats <panel_seats>` (§ 2–5);
  `none` launches no panel. `simplify: yes|no` decides phase 5. Every panel
  seat and simplify reviews only `scope_files:`, and on a range scope only
  the diff of that range; Agent A, being mechanical, checks the whole branch.
- **No brief: the default brief** (`seats=auto; scope=all`). It exists for a
  caller that sends none, an author running `/gaze <pr>` by hand; gaze then
  sizes the panel itself by the same guidance (`panel_seats: auto`,
  `simplify: auto` runs § 5's own rule). An orchestrator (`/raid`, `/hunt`,
  `/merge`) sends a brief.

The result comment echoes the brief and what ran against it in one line
(`references/output.md` § Output shape), so the caller compares the two.

<!-- inline: references/setup-and-breaker.md -->

### 2–5. Review and simplify

Adherence, the review panel and simplify run as laid out in `references/battery.md`, which also holds the optional external reviewer panel. Gaze runs the review panel itself: the seat protocol and the code panel are `references/panel.md`, the prose panel `references/prose-panel.md`; there is no separate review skill and no size tier.

**Which perspectives run** is the brief's (§ The brief): gaze adds no seat and
drops none; only under the default brief does it pick them itself. It picks
each seat's model per launch. The result comment states what ran, by which
model family, and why (§ Output shape); independence is defined in
`skills/route/references/decorrelation.md`.

**Review groups.** No file count stops a review. When the diff is large, the
orchestrator partitions it into review groups, by directory or concern, of
about 400 changed lines or fewer each, and assigns seats per group; a small
diff is one group. The result lists the groups and which seat read which
(`review_groups:`). A group no seat read makes the result FINDINGS, never
REVIEWED, and the result names the unread group.

<!-- inline: references/battery.md -->

<!-- inline: references/panel.md -->

<!-- inline: references/prose-panel.md -->

### 6. Return the review result

Gaze ends here; it runs no gate. Read the phase outputs and return:

```yaml
result: REVIEWED | FINDINGS | ESCALATE
brief: <the caller's brief, or default> → ran: <adherence and each seat that ran>
reviewed_head_sha: <full SHA read from the review worktree after phase 5>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
adherence: PASS | FAIL (<n blocking>)
panel_integrity: COMPLETE | DEGRADED — <PANEL-INTEGRITY: line>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (--force-approve)
review_groups: <group> ← <seats>, ... | one (whole diff)
multi_ticket: <distinct close-claim IDs> | none
```

- `ESCALATE`: a refused brief (§ The brief), a circuit breaker fired, the battery could not run (`battery: NOT-RUN`),
  any phase 2–5 errored or timed out, or the workspace could not be restored.
  `--force-approve` is ESCALATE too, with `battery: skipped (--force-approve)`:
  nothing was reviewed (§ `--force-approve`). So is a DEGRADED panel (below).
  The review did not complete.
- `FINDINGS`: any blocking adherence violation, any `blocking` seat
  verdict, any unresolved `verifiable:` minor, any simplify must-fix
  from this run's pass, an unread review group (§ 2–5). List them.
- `REVIEWED`: none of the above. It is not an approval: `/verify-gate` still
  checks every exit criterion and review comment against the diff.
- `panel_integrity: DEGRADED` (the review panel did not launch, or a selected
  or required perspective has no report after its one retry) means a phase
  2–5 is unresolved, so the result is `ESCALATE` (§ Circuit breakers), whatever
  the perspectives that did report found; it never reads as REVIEWED. A failed
  optional external reviewer is fail-open (§ External reviewer panel) and does
  not count. The `PANEL-INTEGRITY:` line is carried verbatim in the result comment.
- **One retry.** A perspective with no report at the bounded deadline is re-run
  once, alone, over the whole PR, through the panel's ordinary launch
  (`references/panel.md`), before synthesis and posting, so the round does not
  advance. The panel is DEGRADED, hence ESCALATE, only if that retry also has
  no report.

Run the cleanup and containment (`references/cleanup.md`) first, then post the
result as one PR comment (§ Output shape) before returning: cleanup can
downgrade the result to ESCALATE, so the posted result comes after it.

**Attribution.** After each review seat returns, the controller
appends that seat's `reviewer: step=review` line (with its `finding:` lines) to
the PR body through `attribution_record.py --append-pr <pr> --append '<lines>'`
(`$IDH_ROOT/scripts/`). Seats never edit the body; a failed append is reported,
not skipped.

## Cleanup and containment

On every exit path run `references/cleanup.md`: remove this run's review scratch and the review worktree, then check the containment postcondition (cwd, branch, foreign files) and report it before returning control.

<!-- inline: references/cleanup.md -->

## Circuit breakers

- Close claim names a ticket file that does not exist (neither `tickets/<id>-*.erg`
  nor `tickets/closed/<id>-*.erg`; the ticket may already be closed on the branch) → ESCALATE. A PR with
  no ticket at all is not a breaker.
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip).
  Exception: simplify intentionally skipped (adherence blocking, prose
  workpackage, no material growth).
- Telemetry thresholds (`## Telemetry`).

On **every** exit (not only ESCALATE) run `references/cleanup.md` before
returning, so the main repo is never left in a partial state.

## Telemetry and result comment

See `references/output.md`: per-phase timing, the thresholds in `skills/gaze/telemetry.yml`, the override flag and the result comment template.

<!-- inline: references/output.md -->

## Not in scope

- **Gating.** `/verify-gate` rules APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR.
- **Fixing.** Gaze makes no commits; it fixes no finding, simplify's included.
- **Wave-level integration review.** Post-merge integration review of a batch is `/roar` step 8.
- **Merging.** Ever.
