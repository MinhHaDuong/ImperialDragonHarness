---
name: verify
description: Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Never merges.
disable-model-invocation: false
user-invocable: true
argument-hint: <pr-number>
context: fork
---

# Verify PR $ARGUMENTS — six-phase loop with anti-rubber-stamp gate

One skill, one PR, one decision: APPROVED / REROLL / ESCALATE. **Never merges.**
Merge is always the human's or the orchestrator's call.

## When to use

- Orchestrator Phase 6 (per-ticket verification before merge).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use `/review` or `/review-pr` directly.

## Invariants

- Runs on exactly one PR.
- Two gate rounds maximum. Third round is forbidden — escalate instead.
- Never calls `gh pr merge`. The verdict is structured output; the caller decides.
- The fix loop between rounds makes commits on the PR branch; no changes to other branches.
- `--force-approve` is supported for explicit human override; it is logged loudly in the
  PR comments and the skill transcript.
- Only one `/verify` may run per PR per machine at a time. Enforced by an L1 file lock
  (see `## Claim file (L1)`). Cross-machine coordination is out of scope.

## Claim file (L1)

A same-machine concurrency guard that mirrors the `.git/ticket-wip/` pattern used for
ticket claims. Prevents the common collision: two chats / two terminals running
`/verify <same-pr>` simultaneously on the same workstation.

- **Path:** `.git/verify-wip/<pr>.wip` (inside `.git/`, never committed, shared across
  worktrees via `git-common-dir`).
- **Content:** one line — `{ISO-8601-timestamp} {session_id} {worktree-path} round={n}`.
- **Acquire (Phase 1, step 1a):**
  1. If the file does not exist → create it with the current timestamp, session id,
     worktree path, and `round=1`. Proceed.
  2. If the file exists and its timestamp is < 30 minutes old → abort. Print the
     lock file path and its single-line content so the user can find the owning
     session. Do not post a PR comment (the other session is still running and
     will post its own).
  3. If the file exists and its timestamp is ≥ 30 minutes old → treat as stale.
     Delete, recreate with current metadata, and record `L1: stale lock reclaimed
     (previous: <content>)` as an informational line in the final verdict comment.
- **Round 2 re-entry:** the lock is held across rounds. Rewrite the file with
  `round=2` when entering round 2 (same session, updated round marker). Do not
  re-acquire.
- **Release:** delete the file on every terminal path — APPROVED, ESCALATE (including
  round-2 REROLL upgraded to ESCALATE), telemetry-threshold escalation, and
  `--force-approve`. Release must happen **after** the verdict comment is posted,
  so an observer sees the lock tied to the posted outcome.
- **Cross-machine:** not covered. If multi-machine `/verify` collisions become real,
  add a GitHub-label layer (L2) and a monotonic round counter (L3) as a follow-up.
  See ticket 0001 body for the deferred design.

## Phases

### 1. Setup

- **1a. Acquire L1 lock** (see `## Claim file (L1)`). If held by another live session,
  abort before doing any work. If stale, reclaim and record for the verdict comment.
- `gh pr checkout $ARGUMENTS` into an isolated worktree. Abort if the PR is not mergeable
  or if there are open merge conflicts. On abort, release L1.
- Collect:
  - The ticket file referenced in the PR title or body (`tickets/*.erg`).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- If any of these cannot be located, ESCALATE with a clear message and release L1.
  Do not proceed.

### 2–4. Read-only review fan-out (parallel)

Launch in a single message, as background agents:

- `/verify-adherence <branch>` — mechanical-first rule check. If the PR
  carries the `verify:adherence-passed` label (set by `/start-ticket`'s
  pre-PR gate, see PR #40), skip this invocation — the adherence check
  already ran clean before the PR was opened.
- `/review` (built-in) — standard review.
- `/review-pr` or `/review-pr-prose` — file-type heuristic: if any `*.qmd` changed → prose; else code.

Wait for all three to complete. Collect their outputs.

### 5. Simplify (sequential)

After 2–4 land their comments, run `/simplify <pr-number>`. This phase may commit fixes
to the PR branch. Wait for its fixes (if any) to land before the gate reads state.

### 6. Gate (the non-rubber-stamp step)

Invoke `/verify-gate <pr-number>`. It returns a structured verdict:

```yaml
verdict: APPROVED | REROLL | ESCALATE
per_exit_criterion: [...]
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
unresolved_adherence_violations: [...]
rationale: <paragraph>
round: 1 | 2
```

## Branch on verdict

- **APPROVED** → post a "verify: approved" comment on the PR summarising the evidence.
  Release L1. End the skill. The caller merges.
- **REROLL, round 1** → spawn a fix subagent with `isolation: "worktree"`, feeding it the
  unresolved lists as input. Fix agent gets ≤10 min. On push, rewrite the L1 file with
  `round=2` and re-enter phase 6. L1 stays held across the round transition.
- **REROLL, round 2** → upgrade to ESCALATE (no third round). Post a PR comment with the
  still-unresolved items and the gate's rationale. Release L1. End the skill.
- **ESCALATE** → post a PR comment tagged `/verify stopped:` listing what needs human
  judgment. Release L1. End the skill.

## Fix-agent contract

The subagent spawned on REROLL receives:

- Worktree path (PR branch already checked out).
- Unresolved lists from the gate verdict (review comments, simplify findings, adherence
  violations, per-exit-criterion gaps).
- Strict rule: **only** the listed items. No scope creep. No "while I'm here" edits.
- TDD discipline still applies: add a failing test for any behavioural fix before coding.

Push commits to the PR branch; do not open new PRs. Trigger re-entry into phase 6.

## Circuit breakers

- Setup step cannot find ticket file → ESCALATE.
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip).
- Fix agent timeout (10 min) → ESCALATE.
- Gate disagrees with phase 2–5 on a must-fix finding → ESCALATE (no silent resolution).
- Two REROLL rounds reached → ESCALATE.
- Telemetry thresholds (see `## Telemetry`).

## Telemetry

A `/verify` run with no progress signal is indistinguishable from a runaway.
Every run emits runtime + cost so the reader can calibrate.

### Per-phase timing (stderr only)

Before and after each phase (1 setup, 2–4 review fan-out, 5 simplify, 6 gate,
fix-agent rounds), print one line to stderr:

```
[verify] phase=<name> start=<ISO-8601>
[verify] phase=<name> end=<ISO-8601> elapsed=<seconds>s
```

Stderr only — never posted to the PR. Intended for log capture, not review.

### Verdict footer (PR comment)

Append exactly one line to the verdict comment (APPROVED / REROLL / ESCALATE):

```
telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```

- `wall` — seconds from phase-1 start to verdict post.
- `agents` — count of sub-agent invocations (review, review-pr, simplify,
  verify-adherence, fix agent, gate).
- `tokens` — sum of input + output across all sub-agents and the driver,
  as reported by the SDK/agent results. If a sub-agent crashes or does not
  report token counts, use `na` for the missing component (e.g.,
  `tokens=15230+na`); never silently drop the field.
- `cost~=` — best-effort USD estimate using current model rates; `~=` signals
  approximation (ASCII-safe, grep-friendly). If token data is incomplete,
  emit `cost~=na`.

### Thresholds (configurable)

Thresholds are read from `skills/verify/telemetry.yml` at phase-1 start.
Env vars listed in the `env` block override the sibling numeric key when
set and non-empty. Defaults:

| Signal | Warn (continue) | Escalate (stop) |
|--------|-----------------|-----------------|
| Wall   | 15 min          | 30 min          |
| Tokens | 500k            | 1M              |

Behaviour on breach:

- **Warn** → post a short PR comment `/verify: slow run` / `/verify: token-heavy
  run` with the measured value, then continue the run. One warning per signal
  per run (no spam on re-entry for round 2).
- **Escalate** → stop the run, post a `/verify stopped:` comment explaining
  which threshold tripped and the measured value, skip remaining phases. Add
  the telemetry footer before exit so the human sees the numbers that caused
  the escalation. Release L1 after posting.

Escalate takes precedence over warn: if both thresholds are breached at the
same boundary, only escalate. Check thresholds at phase boundaries, not
inside phases — a mid-phase abort leaves the PR in an unclear state.

## `--force-approve`

Explicit human override. Usage: `/verify <pr-number> --force-approve <reason>`.

- Still acquires L1 at setup, then skips phase 6 gate.
- Posts a loud PR comment: `/verify: force-approved — reason: <reason>`. Includes the
  outputs of phases 2–5 so reviewers see what was waived.
- Logs the override in the skill transcript.
- Releases L1 after posting the comment.
- Still does not merge.

## Not in scope

- **Wave-level integration review.** Verify one PR at a time. Use a separate
  `/verify-wave` (not yet drafted) for post-merge integration testing of a batch.
- **Merging.** Ever. That is the caller's job.

## Output shape

Post a single top-level PR comment at end of skill. Template:

```
/verify round=<n> verdict=<V>

Exit criteria:
- <criterion 1>: ADDRESSED — <evidence>
- <criterion 2>: MISSING — <gap>
...

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

Rationale:
<paragraph>

telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```
