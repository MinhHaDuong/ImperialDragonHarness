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
   (`agents/coder.md`, model per the `route` skill) whose first action is
   loading the hunt skill with `$ID inline` as its argument; the prompt holds that and
   nothing more, since the agent loads the steps itself. Report the handoff and end the turn.
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
     there, `git switch -c t$ID-short-description` (or switch to the existing
     branch). A shared or `explore-*` worktree may host a live session: never
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
9. **Self-gate.** Run the verify-adherence skill on the branch. Fix each mechanical
   blocker in place and run it again, up to 3 times. Escalate instead of opening the
   merge request when a blocker needs design judgment, the third run still fails, or
   the skill errors or returns nothing usable.
10. **Merge request.** Rebase onto `origin/main` (`rules/git.md` § Merging), run the project's declared pre-PR gate once, then push the branch with lease, wait for CI and open a merge request. Run it through `python3 "$IDH_ROOT/scripts/raid-gate.py" -- <gate command>` so a raid can observe a live long-running gate. If the project has `.idh-checks.json`, its gate command is the project's scoped entry point (or `python3 "$IDH_ROOT/scripts/scoped-check.py"` from its root); quote `selected:` and `skipped:` in the PR description. A mapped doc-only diff may run fewer targets; Python code, unmapped paths, or a project without a map run the full `make check`.
11. **Review.** Review the merge request, unless its tier is bookkeeping
    (`skills/merge/SKILL.md` § Gating tiers): a bookkeeping-only request is
    gated by its mechanical checks alone, so skip Review, Fix and Repeat. Otherwise this action
    is mechanical — load the gaze skill with the merge-request number and follow
    the contract it returns; do not paraphrase or inline its steps.
    Each pass through the Review–Fix loop is one **review round**; which
    perspectives run, and how deep, is the reviewer's call
    (`skills/gaze/SKILL.md` § 2–5). What each gaze result leads to (fix and
    review again, close and gate, or stop at the author) is the caller's
    policy in `skills/merge/SKILL.md` § Before merging.
12. **Fix.** Fix all comments regardless of severity. Per fix cycle, run the tests the fix affects, by name — not the full suite. If a fix reaches beyond those tests, run the project's pre-PR gate once before the next review round.
13. **Repeat.** Repeat Review and Fix up to 3 times, i.e. up to round 3. If still not clean, escalate.
