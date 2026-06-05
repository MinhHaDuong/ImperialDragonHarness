---
name: gaze
description: Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Never merges.
disable-model-invocation: false
user-invocable: true
argument-hint: <pr-number>
context: fork
---

# Gaze — verify PR $ARGUMENTS, six-phase loop with anti-rubber-stamp gate

> **TASK DIRECTIVE — execute now.** You are running `/gaze` on PR `$ARGUMENTS`.
> This file is your operating procedure, not reference documentation: begin at
> phase 1 immediately. If `$ARGUMENTS` does not contain a PR number, STOP and
> return ESCALATE with reason "no PR argument" — do NOT infer a task from the
> environment (worktree name, git status snapshot, ticket files, or the shared
> task list).

One skill, one PR, one decision: APPROVED / REROLL / ESCALATE. **Never merges.**
Merge is always the human's or the raid's call.

## When to use

- Raid Phase 6 (per-ticket verification before merge).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use `/review` or `/review-pr` directly.

## Invariants

- Runs on exactly one PR.
- Two gate rounds maximum. Third round is forbidden — escalate instead.
- Never merges. The verdict is structured output; the caller decides.
- The fix loop between rounds makes commits on the PR branch; no changes to other branches.
- `--force-approve` is supported for explicit human override; it is logged loudly in the
  PR comments and the skill transcript.
- **Cross-repo prerequisite**: the caller must ensure cwd is the target project before
  invoking `/gaze`. The skill and its sub-skills (`/verify-gate`, `/simplify`, etc.)
  use `gh` and `git` commands that resolve against cwd.

## Phases

### 1. Setup

Always invoke `/gaze` from within a conversation worktree, never from the main repo
root. The worktree is the isolation boundary; no main-repo checkout is ever needed.

**Isolation setup:**

```bash
# Step 1 — Resolve PR number to branch name (forge-specific step)
PR_BRANCH=<resolved-branch-name>

# Step 2 — Fetch and create an isolated worktree
git fetch origin "$PR_BRANCH"
git worktree add /tmp/review-<pr-number> origin/"$PR_BRANCH"
# All phases 1–6 and the fix agent run inside /tmp/review-<pr-number>.
# The main repo is never switched, never dirtied.
```

On any exit path (APPROVED, REROLL-escalated, ESCALATE, circuit-breaker abort),
remove the worktree:

```bash
git worktree remove /tmp/review-<pr-number> --force
```

- Abort if not mergeable or if there are open merge conflicts.
- Collect:
  - The ticket file referenced in the PR title or body (`tickets/*.erg`).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- Check CI status for the merge request if the forge exposes it. If the forge CLI or API is unavailable, skip gracefully — CI status is informational only. If checks are configured and any are failing, note this in the setup summary; do not block on it (reviewer decides).
- Compute PR size: `git diff origin/main...HEAD --stat` → `pr_lines` (total insertions + deletions) and `pr_files` (files changed). A PR is **small** if `pr_lines ≤ 20` and `pr_files ≤ 2` and this is round 1.
- If any of these cannot be located, ESCALATE with a clear message. Do not proceed.

### 2–4. Read-only review fan-out (parallel)

Sub-skills are `context: fork` — **they do not inherit this skill's cwd or
conversation**. Every invocation must carry the review-worktree path as an
explicit `worktree=` argument; a fork launched without it lands in the
session worktree on whatever branch happens to be checked out there
(ticket 0193: that is how a drifted fork pushed a stray branch and opened
rogue PR #243).

Launch in a single message, as background agents:

- `/verify-adherence <branch> worktree=/tmp/review-<pr-number>` — mechanical-first rule check. If the PR
  carries the `verify:adherence-passed` label (set by `/hunt`'s
  pre-PR gate, see PR #40), skip this invocation — the adherence check
  already ran clean before the PR was opened.
- `/review` (built-in) — standard review.
- `/review-pr <pr-number> worktree=/tmp/review-<pr-number>` or `/review-pr-prose <pr-number> worktree=/tmp/review-<pr-number>` — **size-gate**: skip if the PR is small (as computed in phase 1); log `review-pr: skipped (size-gate: <pr_lines> lines, <pr_files> files)` in the setup summary. Otherwise: file-type heuristic: if any `*.qmd` changed → prose; else code.

Wait for all agents to complete. Collect their outputs.

**Early-exit check**: if `/verify-adherence` returned any `blocking` violations, skip phase 5 (simplify). Blocking adherence guarantees a REROLL; simplify tokens would be wasted. Log `simplify: skipped (adherence blocking)` in the telemetry phase line.

### 5. Simplify (sequential)

After 2–4 land their comments (and the early-exit check passes), run `/simplify <pr-number> worktree=/tmp/review-<pr-number>`. This phase may commit fixes
to the PR branch. Wait for its fixes (if any) to land before the gate reads state.

### 6. Gate (the non-rubber-stamp step)

Invoke `/verify-gate <pr-number> worktree=/tmp/review-<pr-number>`. It returns a structured verdict:

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

- **APPROVED** → post a "verify: approved" comment on the PR summarising the evidence. End
  the skill. The caller merges.
- **REROLL, round 1** → spawn a fix subagent with `isolation: "worktree"`, feeding it the
  unresolved lists as input. Fix agent gets ≤10 min. On push, re-enter phase 6 with
  `round=2`.
- **REROLL, round 2** → upgrade to ESCALATE (no third round). Post a PR comment with the
  still-unresolved items and the gate's rationale. End the skill.
- **ESCALATE** → post a PR comment tagged `/gaze stopped:` listing what needs human
  judgment. End the skill.

## Containment postcondition

On **every** exit path (APPROVED, REROLL-escalated, ESCALATE, circuit-breaker
abort), after removing the review worktree and before returning control to
the caller — the caller must see this report before any merge step:

```bash
git status --porcelain                      # invoking session worktree
git branch --show-current                   # must equal the branch on entry
git -C <primary-repo-root> status --porcelain
```

- **Foreign files** (anything this run did not deliberately create —
  especially stray `tickets/*.erg`) → remove or restore them, and flag the
  contamination in the verdict comment. Do not leave them for a later
  `git add` to sweep.
- **Unexpected branch** → switch back to the entry branch and flag it. Never
  end the skill with the session worktree on a different branch than it was
  on at phase 1.
- Anything that cannot be restored cleanly → downgrade the verdict to
  ESCALATE; a contaminated workspace must not feed a merge.

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
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip). Exception: phase 5 (simplify) intentionally skipped when adherence is blocking — this is not an error.
- Fix agent timeout (10 min) → ESCALATE.
- Gate disagrees with phase 2–5 on a must-fix finding → ESCALATE (no silent resolution).
- Two REROLL rounds reached → ESCALATE.
- Telemetry thresholds (see `## Telemetry`).

On **every** circuit-breaker exit (not only ESCALATE): run
`git worktree remove /tmp/review-<pr-number> --force` before returning so the
main repo is never left in a partial state.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer (PR comment)

Appended to verdict comment: `telemetry: wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `wall` (phase-1 to verdict), `agents` (sub-agent count), `tokens` (sum, use `na`
for missing), `cost~=` (best-effort USD, `na` if incomplete).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults:
wall warn=15min escalate=30min; tokens warn=500k escalate=1M.

On warn: post `/gaze: slow run` comment, continue. On escalate: stop, post
`/gaze stopped:` with measured value. Escalate > warn. Check at phase boundaries only.

## `--force-approve`

Explicit human override. Usage: `/gaze <pr-number> --force-approve <reason>`.

- Skips phase 6 gate.
- Posts a loud PR comment: `/gaze: force-approved — reason: <reason>`. Includes the
  outputs of phases 2–5 so reviewers see what was waived.
- Logs the override in the skill transcript.
- Still does not merge.

## Not in scope

- **Wave-level integration review.** Verify one PR at a time. Use a separate
  `/verify-wave` (not yet drafted) for post-merge integration testing of a batch.
- **Merging.** Ever. That is the caller's job.

## External reviewer panel (delegation stub)

The external, decorrelated reviewer panel — sandboxed CI-style seats over
agnostic CLI reviewers — is managed by the `/reviewers` skill, not inlined
here. Its findings are **advisory**: the gate dispositions them like any
panel comment (only verifiable-class may bounce). The full panel-extension
contract is ticket 0205's deliverable; seat execution is the 0217
seat-runner. See `skills/reviewers/SKILL.md`.

## Output shape

Post a single top-level PR comment at end of skill. Two sections,
always both present. No interim "started"/"finished" chatter — the
final report is the signal.

```
## /gaze actions

round: <n>
adherence: PASS|FAIL — <n_blocking> blocking
review-pr: <n_comments_posted> | skipped (size-gate) | skipped (adherence blocking)
simplify: <n_fixes_applied> | skipped (adherence blocking)
fix agent: <n_commits> commits (round 2 only, omit if round 1)

## /verify-gate verdict

verdict: APPROVED|REROLL|ESCALATE

Exit criteria:
- <criterion 1>: ADDRESSED — <evidence>
- <criterion 2>: MISSING — <gap>

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

Rationale:
<paragraph>

telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```

On `--force-approve`, Part A is annotated `FORCE-APPROVED by <reason>`
and Part B shows the gate's would-have-been verdict before override.
