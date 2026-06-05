---
name: raid
description: Run an Imperial Dragon raid across multiple tickets. Picks targets, manages waves, enforces isolation. Merges APPROVED PRs after verify-gate clears.
disable-model-invocation: false
user-invocable: true
argument-hint: [ticket-ids or "all open"]
model: claude-opus-4-6
effort: max
---

# Raid $ARGUMENTS — Imperial Dragon hunt

A raid does not redefine skills. It calls `/start-ticket`,
`/review-pr`, `/roar`, etc. Its job is sequencing, wave management,
and enforcing invariants.

## Balance rule

**Deliverable work ≥60%, tooling ≤40%.** If two consecutive tickets were tooling, the next must advance a deliverable. Track in session log.

**Deliverables**: items in `STATE.md` under current milestone — papers, slides, reading notes, figures, responses to reviewers. Tooling: tests, hygiene, refactoring, harness improvements.

**Escape hatch**: if `make check-fast` fails and blocks all deliverable work, tooling may exceed 40%. Document why.

## Checkpointing

Every phase ends with a git commit. If the session dies, resume by
reading the ticket logs and git history to determine which phase
completed last. The checkpoint is the repo, not session state.

## Phase 1: Select

If $ARGUMENTS is "all open": read open tickets from git-erg `tickets/` or forge.
Otherwise: parse comma-separated ticket IDs.

Prioritize:
1. Scientific deliverables first
2. Gaps with north star (STATE.md)
3. Ripest open issues
4. Inline markers (FIXME, TODO, HACK)

Read each ticket + STATE.md. Group by milestone. Identify dependency order and wave structure.

## Phase 2: Imagine (parallel)

For each ticket, launch an agent (background, no isolation needed — read-only):
- Read ticket + STATE.md + surrounding code
- Reimagine: why now, why this scope, what's the simplest path
- **Antipattern scan (scope).** YAGNI (search the package registry —
  don't hand-roll what a library already does), premature abstraction.
  Annotate any hits with the proposed fix.

Wait for all. Commit reimagined tickets. Report scorecard.

**Drift guard**: For each reimagined ticket, compare against the original:
- Exit criteria dropped or reworded to change intent → ESCALATE.
- New exit criteria added that weren't implied by the original → ESCALATE.
- Scope narrowed to a strict subset of the original → allowed (simplification).
- Implementation approach changed but exit criteria preserved → allowed (that's the point).

Reimagination refines *how* to deliver, not *what* to deliver. Any ticket that
fails the drift guard is pulled from the raid and left for human review with
a comment explaining what the Imagine agent proposed to change and why.

## Phase 3: Plan (parallel)

For each reimagined ticket, launch an agent (background):
- Read ticket + actual source code
- Write Actions, first test, dependencies
- **Antipattern scan.** Tautological tests — would this test catch a
  wrong implementation, or only a different one? Annotate any hits
  with the proposed fix.

Wait for all. Commit planned tickets. Report scorecard. Ticket files go on a
branch — stage and commit the `.erg` file immediately after writing it; if
staging fails (gitignore or wrong cwd), embed the ticket content directly in
the execute agent prompt and the agent creates the file as its first step.

## Phase 4: Verify feasibility

Launch agents by cluster to cross-check plans:
- File paths, line numbers, function signatures
- Data assumptions, API key requirements
- Cross-ticket conflicts
- Cross-cutting registries: a file holding a shared hash-set / dict / dispatch
  table (test allowlist, dispatch keys, config conventions) that 3+ PRs will
  edit. Flag any you find — they trigger the Phase 5.0 coordination PR.

Annotate tickets with PASS/WARN/BLOCK. Commit annotations.

## Phase 5.0: Land coordination PR (cross-cutting registries)

**When**: 3+ PRs in a wave will edit the same file holding a shared
hash-set / dict / dispatch registry (test allowlists like `VALID_ROUTES`,
dispatch keys, config-file conventions). If ≤2 PRs touch it, skip — a manual
rebase is cheaper than the coordination overhead.

**Why**: when N parallel PRs each append to the same cross-cutting set, the
rebase onto sibling-merged main silently drops each PR's own addition. Wave 2
(SOTA-adapter raid, 2026-05-20) needed a resurrection agent for 3 of 4 merges
because of this. (memory: feedback_rebase_drop_cascade)

**How**: before opening any Wave-N PR, open one tiny PR that adds ALL of the
wave's entries to the shared registries at once, and merge it first. Each
Wave-N PR then makes a purely additive change (new file, new entry referencing
a pre-registered key) without mutating the shared set. The coordination PR
itself follows the normal verify/merge gates.

## Phase 5: Execute (waves, worktree-isolated)

Group tickets into waves:
- Wave N: no unmerged dependencies
- Wave N+1: depends on Wave N results

For each wave, launch agents with `isolation: "worktree"`.
Each agent follows `/start-ticket` workflow. Push branch when done, create merge request.

Wait for wave to complete.

## Phase 6: Verify (per-ticket `/verify`)

Mood: Be strict, skeptical, nit-picky, detail-oriented. Aim for code excellence and integrity.

**Per-ticket:** launch per-ticket `/verify` runs in parallel (background agents,
one per merge request) when the PR branches touch disjoint files. Verify
file-sharing PRs sequentially to avoid concurrent-fix collisions. Respect the
max-concurrent-agents cap (see Subagents in rules/workflow.md). Phase 7 merges
stay strictly sequential.

**Per-wave:** after all per-ticket `/verify` runs complete, launch one integration-review
subagent (read-only) to check:
- Do the merged/merge-pending PRs compose without contradiction?
- Does `make check` still pass if we imagine them all merged?
- Are there testing gaps visible only at wave granularity (e.g., two PRs touching the
  same test file in incompatible ways)?

Wave-level findings go to the human as a wave-summary comment; they do not block
individual `/verify` verdicts.

## Phase 7: Merge (sequential per-wave)

**Token economy rule**: Any time a ticket must be created in any phase, invoke
`/ticket-new` — never write the file directly or compute the next ID manually.
`/ticket-new` calls `erg next-id` and `erg validate <file>` (file arg, not
directory), keeping mechanical work inside the tool where it belongs.

**Bundle follow-up tickets into the spawning PR.** When a raid or review
surfaces a follow-up, open it via `/ticket-new` and commit the `.erg` onto the
current PR branch — the ticket only, never the fix. Reference it from the PR
body (`Related follow-up: tickets/NNNN`, or `Scope overflow: tickets/NNNN` when
it comes from a verify-gate verdict). The PR's `**Ticket:**` line still closes
only its own ticket on merge; the bundled follow-up stays open. Never file the
follow-up on a main checkout — main is read-only and may be dirty with parallel
work.

For each wave, merge APPROVED PRs one at a time. A PR is merge-eligible if:
- `/verify-gate` verdict is APPROVED (one REROLL allowed — Phase 6 handles this), AND
- `scope_overflow` in the verdict is empty or all entries have suggested disposition
  TICKETED (caller creates tickets via `/ticket-new` and adds `Scope overflow:
  tickets/NNNN` to the PR body before merging).

Any ESCALATE verdict (from exit criteria, review comments, or scope overflow) stops
the PR — it stays open for human review.

For each eligible PR, sequentially within the wave:
1. `git fetch origin` to pick up any prior merges.
2. `gh pr checkout <pr-number>` — `/merge` requires being on the PR head branch. <!-- harness-extension-point -->
3. Check PR is still mergeable (no conflicts from earlier merges in this wave).
4. Run `/merge <pr-number>`. This atomically closes the ticket and merges via GitHub API.
5. If merge fails (conflict, CI regression), ESCALATE — leave a PR comment and move to the next PR.

After all waves: `git checkout main && git pull --rebase origin main`, then
`make check`. New failures → revert last merge + ticket.

## Phase 8: Celebrate (per-merged-PR)

After all merges, from the updated main branch, run `/roar` for each
successfully merged PR. The roar pre-check (`git merge-base --is-ancestor
HEAD origin/main`) passes because HEAD is main after the pull.

## Mid-session checkpoint (~50% effort)

- [ ] Opened at least one deliverable-forward merge request?
- [ ] Tooling/deliverable ratio within bounds?
- [ ] Self-reviewed at least one merge request?
- [ ] `make check` passes on main?

Autonomous mode: ralph loop to next wave.

## Wrap up

1. `make check` on main — compare against baseline. New failures → ticket.
1b. Scan all tickets for bump lines and print a tally:
    ```
    grep -h ' bump ' tickets/*.erg | awk '{print $4}' | sort | uniq -c | sort -rn
    ```
    Format as: `Ticket NNNN: N bumps (X permission, Y verify-reroll, …) → Z% trivial`
2. All merged PRs confirmed on main. Any ESCALATED PRs listed with reasons.
3. Write briefing (session log + merge request list + test delta).
4. Do NOT run `/lair`.

## Circuit breakers

All three triggers below require a bump log line written to the **main-repo**
`tickets/` directory (not the killed agent's worktree copy), committed before
relaunching: `{ISO8601} claude bump circuit-breaker — {reason}`.

**Killing a mid-execution agent — salvage WIP first.** Before any
`git worktree remove` on a killed agent's worktree, salvage its work so it
survives the deletion:

```bash
~/.claude/scripts/worktree-salvage.sh <worktree-path>
```

This commits everything on the agent's branch and pushes it. A PreToolUse guard
enforces the order: `git worktree remove` is blocked while the worktree has
uncommitted changes. Relaunch the finisher on the **existing** branch with
`git switch <branch>` (NOT `-c`); it inspects the salvaged WIP via
`git show --stat HEAD` before continuing rather than starting from scratch.
Salvage is the FIRST step of any restart, not an afterthought.
(memory: feedback_killed_agent_salvage)

**Agent timeout**: If an agent has not pushed within 10 minutes, salvage its
worktree (above), then kill it. Split the ticket or relaunch with narrower
scope. Bump reason: `agent timeout`.

**Ping-pong detector**: If two agents edit the same file on the
same branch, STOP. Reset to last known-good commit, relaunch ONE agent.
Bump reason: `ping-pong on {file}`.

**Redirect ban**: Do not use SendMessage to redirect a running
agent. Kill and relaunch with corrected instructions.
Bump reason: `redirect ban triggered`.

**Escalation**: If the same fix fails twice, stop and leave a
ticket comment with the two failed approaches.
