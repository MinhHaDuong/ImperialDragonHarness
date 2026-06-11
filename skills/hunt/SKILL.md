---
name: hunt
description: Begin work on a ticket. Creates worktree, writes first test, transitions to Execute phase.
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
3. Enter the ticket's **own** worktree: unless the current worktree is already named
   `t$ARGUMENTS`, call `EnterWorktree` with name `t$ARGUMENTS` — even if the session
   already sits inside some other worktree. "Already in a worktree" is NOT isolation:
   a shared or `explore-*` worktree may host a live session, and a hunt must never
   rebase, branch, or leave uncommitted files in a worktree it does not own
   (2026-06-11: a hunt inherited an orchestration session's worktree, rebased its
   branch, and stranded in-progress test edits there). Before the first
   branch-mutating command, confirm ownership:
   `basename "$(git rev-parse --show-toplevel)"` must be exactly `t$ARGUMENTS`
   (rules/git.md § anchor branch-mutating git across a forked-skill boundary).
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
