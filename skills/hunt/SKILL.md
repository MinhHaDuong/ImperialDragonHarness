---
name: hunt
description: Begin work on a ticket — creates a worktree and writes the first test.
disable-model-invocation: true
user-invocable: true
argument-hint: <ticket-id>
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
3. Enter the ticket's **own** worktree, or confirm the spawner already gave you one.
   A worktree is **owned** when either its basename is exactly `t$ARGUMENTS`, OR its
   basename matches `agent-*` (the orchestrator created it for this agent session) AND
   `git status --porcelain` prints nothing — the session started inside it and its tree
   is clean (that is what `Agent(isolation:"worktree")` produces). Both conditions must
   hold: an `agent-*` basename over a dirty tree is not proof of ownership. A shared or
   `explore-*` worktree that may host a live session is **not
   owned**: a hunt must never rebase, branch, or leave uncommitted files in a worktree
   it does not own (2026-06-11: a hunt inherited an orchestration session's worktree,
   rebased its branch, and stranded in-progress test edits there). Resolve ownership
   before the first branch-mutating command:
   - Already inside an owned worktree — basename `t$ARGUMENTS`, or an `agent-*`
     one from an `Agent(isolation:"worktree")` spawn whose `git status --porcelain` is
     empty — means you are isolation-confirmed; proceed to step 4. When such a spawned
     agent has its `EnterWorktree` rejected with "already in a worktree", that rejection
     **is** the confirmation only if the current tree passes the same clean `agent-*`
     check; a rejection over a dirty or non-`agent-*` tree means STOP — the worktree is
     not owned — not an error to proceed through.
   - Otherwise call `EnterWorktree` with name `t$ARGUMENTS`, even if the session already
     sits inside some other, unowned worktree.
   Confirm with `basename "$(git rev-parse --show-toplevel)"`: it must be `t$ARGUMENTS`
   or the `agent-*` worktree of this session (rules/git.md § anchor branch-mutating git
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
8. Announce `[Plan → Execute]`, then implement until `make check` passes.
9. Pre-PR self-gate: run `/verify-adherence <branch>` (the branch created in step 4).
   - Clean → proceed to step 10. Note adherence passed in the merge-request description so `/gaze` can skip the mechanical phase on its next pass.
   - Blockers → decide per blocker:
     - Cheap and mechanical (obvious fix, no design judgement) → fix in place, re-run `make check` and `/verify-adherence`, then proceed only once clean. Up to 3 fix-and-recheck cycles; if still not clean after 3 rounds, escalate.
     - Otherwise → STOP. Do not open the PR. Escalate with the adherence report and the blocker list.
   - Circuit breaker: if `/verify-adherence` itself errors, times out, or returns an unparseable result → ESCALATE. Do not open the PR and do not silently skip the gate.
10. Push the branch and open a merge request.
11. Review according to `/review-pr`.
12. Fix all comments regardless of severity.
13. Repeat 11–12 up to 3 times. If still not clean, escalate (see workflow rules).
