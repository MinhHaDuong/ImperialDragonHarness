---
name: hunt
description: Begin work on a ticket — creates a worktree and writes the first test.
disable-model-invocation: false
user-invocable: true
argument-hint: <ticket-id> [inline]
---

# Hunt — begin work on ticket $ARGUMENTS

`[Plan → Execute]`

## Steps

1. Read the ticket (from git-erg `tickets/` directory or forge).
2. Check the **Exit criteria** section. If unclear, ask the author before writing code.
   - If all exit criteria are **already met** (verify by inspection/grep before writing any code),
     close the ticket through the **normal branch + PR flow** — never commit the close on `main`.
     Enter the worktree (step 3) and create the branch (step 4) first, then on that branch run
     `${ERG:-tickets/erg} close $ARGUMENTS already-done`, commit the ticket file
     (`git add -u tickets/ && git commit -m "ticket($ARGUMENTS): close — already-done"`
     — `-u` stages the close edit and any dependent Blocked-by removals, never a
     stray file in the shared `tickets/`), and open the
     merge request (step 10). Skip the test/implement steps (5–9); the merge request lands the close
     via review like any other change. Do not stop with an uncommitted-to-`main` or unpushed close.
2b. **Route before you execute.** This triage runs once, at hunt entry, before any
   code is written. Step 2's already-met fast path never reaches it, and needs no
   triage: it executes nothing, it only lands a close through the normal PR flow.
   Of the hunts that do arrive here, three skip it entirely and proceed straight to step 3:
   an executor already running detached, identified by step 3's worktree ownership
   check (that check is the sole discriminator — do not restate its conditions
   here); a hunt the author invoked with an explicit `inline` argument, which
   keeps the co-working behaviour in the author's own session — arguments are
   `<ticket-id>` optionally followed by `inline`, so the ticket id is the
   leading token of `$ARGUMENTS` and is what every `t$ARGUMENTS` worktree name
   and `${ERG:-tickets/erg} close $ARGUMENTS` substitution in this file refers
   to; and a headless run
   (`claude -p "/hunt <id>"`), which is already the detached case an orchestrator
   asked for. Only a hunt in the author's live interactive session reaches the
   fork below.
   Each skip is total, the needs-human branch included: an executor spawned by an
   interactive hunt was triaged by that hunt before it was spawned, so re-reading
   the tells buys nothing. A raid, though, picks its own targets and no
   interactive hunt precedes them. `erg ready` already skip-lists the label out
   of pick-ticket's queue (`tickets/.ergrc`), and raid Phase 1 now screens its
   own targets ([[0390]]); neither is a second triage here.
   - **Needs-human triage.** Read the ticket for these tells, mostly mechanical: a
     `Label: needs-human` header; exit criteria carrying decision verbs (decide,
     arbitrate, sign-off, choose among); manuscript prose as the deliverable, which
     rules/git.md § Prose workpackages already reserves for author arbitration; a
     premise resting on conflicting sources. On a hit, do not execute and write no
     code. Return ONE batched decision list to the author, each item with a
     recommended default, and end the turn. That return is a success outcome of the
     hunt, not a failure, exactly as the raid drift guard treats a premise objection.
   - **Detach by default.** No tell hit, and the hunt is running in the author's
     interactive session: hand the ticket to ONE background worktree-isolated
     agent. Not a raid — for a single ticket its orchestrator and review panels
     cost more than the ticket returns. Launch with `isolation: "worktree"` and
     `model: opus` (raid § Model policy, where coders keep the top tier; effort is
     the session effort, run at `high`). The agent's FIRST action is mechanical:
     ```
     Skill(skill: "hunt", args: "$ARGUMENTS")
     ```
     The launch prompt must NOT paraphrase, summarize, or inline hunt's steps;
     `skills/hunt/SKILL.md` is the single live execution contract and the loader
     supplies it fresh on every run (mirrors raid Phase 5). Instruct the agent to
     push its branch and open a merge request as hunt's flow dictates. Then report
     the handoff and end the turn: the interactive session stays at decision
     altitude instead of accumulating the executor's test dumps, diffs, and review
     rounds, which measured 5.4x the cost of the same contract run detached.
3. Enter the ticket's **own** worktree, or confirm the spawner already gave you one.
   A worktree is **owned** when either its basename is `t$ARGUMENTS` or begins with
   `t$ARGUMENTS-` (the collision-resistant suffixed form — see the `EnterWorktree`
   call below), OR its basename matches `agent-*` (the orchestrator created it for this agent session) AND
   `git status --porcelain` prints nothing — the session started inside it and its tree
   is clean (that is what `Agent(isolation:"worktree")` produces). Both conditions must
   hold: an `agent-*` basename over a dirty tree is not proof of ownership. A shared or
   `explore-*` worktree that may host a live session is **not
   owned**: a hunt must never rebase, branch, or leave uncommitted files in a worktree
   it does not own (2026-06-11: a hunt inherited an orchestration session's worktree,
   rebased its branch, and stranded in-progress test edits there). Resolve ownership
   before the first branch-mutating command:
   - Already inside an owned worktree — basename `t$ARGUMENTS` or beginning with `t$ARGUMENTS-`, or an `agent-*`
     one from an `Agent(isolation:"worktree")` spawn whose `git status --porcelain` is
     empty — means you are isolation-confirmed; proceed to step 4. When such a spawned
     agent has its `EnterWorktree` rejected with "already in a worktree", that rejection
     **is** the confirmation only if the current tree passes the same clean `agent-*`
     check; a rejection over a dirty or non-`agent-*` tree means STOP — the worktree is
     not owned — not an error to proceed through.
   - Otherwise call `EnterWorktree` with name `t$ARGUMENTS-<pid>`, where `<pid>`
     is the session PID — a discriminator that keeps parallel sessions on the same
     ticket in distinct worktree paths. Resolve it to a literal first (the
     `EnterWorktree` name schema rejects `$` characters): run `bash -c 'echo $$'`
     and substitute the number, e.g. pass `t$ARGUMENTS-12345`, not the raw
     `t$ARGUMENTS-$$`. Call `EnterWorktree` even if the session already sits inside
     some other, unowned worktree.
   Confirm with `basename "$(git rev-parse --show-toplevel)"`: it must be `t$ARGUMENTS`,
   begin with `t$ARGUMENTS-`, or be the `agent-*` worktree of this session (rules/git.md § anchor branch-mutating git
   across a forked-skill boundary). Ad hoc orchestrators should not hand-type this
   ownership contract: spawn the hunt headlessly as `~/.claude/scripts/beat.py` does, with
   `claude -p "/hunt <id>"`, so the live SKILL.md text supplies the rule.
4. Create or checkout the ticket branch:
   ```bash
   git switch -c t$ARGUMENTS-short-description
   ```
5. Read the files listed in **Relevant files**.
6. Write the first test from the **Test** section of the ticket.
7. Run `make check-fast` — confirm the test fails.
8. Announce `[Plan → Execute]`, then implement until `make check-fast` (or the affected test file alone) passes — that is the loop gate. Full `make check` runs once, immediately before step 10 opens the PR — not per edit.
9. Pre-PR self-gate: run `/verify-adherence <branch>` (the branch created in step 4).
   - Clean → proceed to step 10. Note adherence passed in the merge-request description so `/gaze` can skip the mechanical phase on its next pass.
   - Blockers → decide per blocker:
     - Cheap and mechanical (obvious fix, no design judgement) → fix in place, re-run `make check-fast` and `/verify-adherence`, then proceed only once clean. Up to 3 fix-and-recheck cycles; if still not clean after 3 rounds, escalate.
     - Otherwise → STOP. Do not open the PR. Escalate with the adherence report and the blocker list.
   - Circuit breaker: if `/verify-adherence` itself errors, times out, or returns an unparseable result → ESCALATE. Do not open the PR and do not silently skip the gate.
10. Run the full `make check` once, then push the branch and open a merge request.
11. Review the merge request. This action is mechanical — invoke the review-pr
    skill with the PR number:
    ```
    Skill(skill: "review-pr", args: <pr-number>)
    ```
    Follow the contract the skill loader returns; do not paraphrase or inline its
    steps (mirrors raid Phase 5's mechanical `Skill(hunt)` invocation, ticket 0293).
    Each pass through the 11–12 loop is one **review round**. Do not pass a round
    number: `/review-pr` derives its own round from the merge request's posted
    review history and scopes the panel accordingly — round 1 runs the full
    proportional panel, later rounds re-run only the perspectives that objected
    plus a regression check (§ Round scoping in `skills/review-pr/SKILL.md`,
    ticket 0377).
12. Fix all comments regardless of severity. Per fix cycle, run `make check-fast` plus the tests implicated by the comments — not the full suite. If any cycle's fix touches code outside the fast tier, run the full `make check` once, in addition — not on every cycle.
13. Repeat 11–12 up to 3 times, i.e. up to round 3. If still not clean, escalate (see workflow rules).
