---
metadata:
  category: build
name: hunt
description: "Work a ticket — creates a worktree, TDD code, open merge request, review and fix."
disable-model-invocation: false
user-invocable: true
argument-hint: "<ticket-id> [inline]"
---

# Hunt — begin work on ticket $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

## Steps

1. **Detach.** <!-- Fresh subagent to conserve the live session context. -->
   Arguments are `<ticket-id> [inline]`; `$ID` is the ticket id.
    - Without `inline`, hand the ticket to one background agent with the coder profile
   (`agents/coder.md`) whose first action is
   loading the hunt skill with `$ID inline` as its argument; the prompt holds that and
   nothing more, since the agent loads the steps itself. Report the handoff and end the turn.
   Choose the model of each launched worker per launch, from the `route` skill grid
   (`skills/route/SKILL.md`); seats that must be independent follow
   `skills/route/references/decorrelation.md` ("The launch line").
    - With `inline` (the detached agent, a raid, a headless run, or the author co-working),
   go on in the current context.
2. **Read.** Read ticket `$ID` (from git-erg `tickets/` directory or forge).
3. **Triage.** Check the ticket's **Exit criteria** section.
   - Judgment needed — criteria unclear, a `Label: needs-human` header, criteria
     that decide, arbitrate, sign off or choose, manuscript prose as the
     deliverable, a premise resting on conflicting sources: settle each by
     `rules/workflow.md` § Escalation protocol (advisor model first) before coding.
   - Already met: write no code. After Worktree, record the evidence with
     `${ERG:-tickets/erg} log $ID "already met: <evidence>"`, commit it,
     and go straight to Merge request; its ticket claim closes the ticket at merge.
   - Premise expired: check what changed on the ticket's **Relevant files** since its
     `Created` date (`git log --since=<Created> -- <files>`). If a change voids the
     premise, write no code and settle it by the same escalation protocol. Confirmed
     obsolete: log `"obsolete: <commit or change>"` and go to Merge request as for
     already met. Still valid but worded for an old tree: update the ticket on the
     branch and continue.
4. **Worktree.** Work in the ticket's **own** worktree, on its own branch.
   - **Owned already?** Yes if you created it for this ticket, or the spawner
     handed it to you by path with `git status --porcelain` printing nothing:
     there, `W=$(git rev-parse --show-toplevel)` and `git switch -c t$ID-short-description`
     (or switch to the existing branch). A shared or `explore-*` worktree may host a live session: never
     rebase, branch, or leave files in it.
   - **Otherwise create one** under the primary checkout. `P=$PPID`, the
     long-lived runtime process, names the path and owns the lock (pid 1 or
     other edge cases: `references/worktree-lifecycle.md`):
     ```bash
     R=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
     W=$R/.claude/worktrees/t$ID-$P
     git worktree add "$W" -b t$ID-short-description origin/main
     git worktree lock --reason "hunt t$ID (pid $P)" "$W"
     ```
     If the branch already exists (re-hunt, second session), drop `-b`:
     `git worktree add "$W" <branch>`. Without `origin/main`, use `main`.
   - **Register and enter.** `python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$W"`,
     then `cd "$W"`. Work only there: absolute paths under it, `git -C "$W"` for git.
     Scratch files go in `$W/.tmp/`: set `TMPDIR="$W/.tmp"` per command, never for
     the whole session. Evidence and deliverables stay outside `.tmp/`.
5. **Relevant files.** Announce `[Plan → Execute]`, then read the files listed in **Relevant files**.
6. **Test.** Write the tests the ticket's **Test** section asks for. Tag each one
   like the project's existing tests: its speed tier (Python: `rules/coding-python.md`
   § Testing) and, in a modular project, its module.
7. **Fail first.** Run the new tests by name (e.g. `pytest <file>::<test>`); confirm each one runs and fails for the expected reason.
8. **Implement.** Implement until those tests pass, rerunning them by name as the loop gate.
9. **Self-gate.** Announce `[Execute → Verify]`, then run the verify-adherence skill on the branch. Fix each mechanical
   blocker in place and run it again, up to 3 times. Escalate instead of opening the
   merge request when a blocker needs design judgment, the third run still fails, or
   the skill errors or returns nothing usable.
10. **Merge request.**
    - Rebase onto `origin/main` (`rules/git.md` § Merging).
    - Run the project's fast test tier once (Python: `make check-fast`,
      `rules/coding-python.md` § Testing).
    - Push with lease and open the merge request. Its description carries the
      close claim `**Ticket:** tickets/<ticket file>`. Wait for CI where it runs on the branch.
11. **Review.** Skip when
    `python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base origin/main --head HEAD`
    exits 0 (bookkeeping). Otherwise run up to 3 rounds: load the gaze skill with the
    merge-request number; on findings, fix every comment whatever its severity, rerun
    the tests the fixes affect by name, then the fast test tier, push, and review again.
    Escalate when gaze does, or when round 3 still has findings.
