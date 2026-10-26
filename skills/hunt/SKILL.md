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
   `Skill(skill: "hunt", args: "$ID inline")`; the prompt holds that call and
   nothing more, since the agent loads the steps itself. Report the handoff and end the turn.
    - With `inline` (the detached agent, a raid, a headless run, or the author co-working),
   go on in the current context.
2. **Read.** Read ticket `$ID` (from git-erg `tickets/` directory or forge).
3. **Triage.** Check the ticket's **Exit criteria** section.
   - Judgment needed — criteria unclear, a `Label: needs-human` header, criteria
     that decide, arbitrate, sign off or choose, manuscript prose as the
     deliverable, a premise resting on conflicting sources: settle each by
     `rules/workflow.md` § Escalation protocol (advisor model first) before coding.
   - Already met: write no code. After Worktree and Branch, record the evidence with
     `${ERG:-tickets/erg} log $ID "already met: <evidence>"`, commit it,
     and go straight to Merge request; its ticket claim closes the ticket at merge.
   - Premise expired: check what changed on the ticket's **Relevant files** since its
     `Created` date (`git log --since=<Created> -- <files>`). If a change voids the
     premise, write no code and settle it by the same escalation protocol. Confirmed
     obsolete: log `"obsolete: <commit or change>"` and go to Merge request as for
     already met. Still valid but worded for an old tree: update the ticket on the
     branch and continue.
4. **Worktree.** Work in the ticket's **own** worktree. A worktree is **owned** when you created
   it for this ticket, or the spawner handed it to you by path with
   `git status --porcelain` printing nothing. A shared or `explore-*` worktree that
   may host a live session is **not owned**: a hunt must never rebase, branch, or
   leave uncommitted files in it (a hunt that inherited an orchestration
   session's worktree once rebased its branch and stranded in-progress test edits). Otherwise create one with plain git under the primary checkout,
   `<pid>` from `bash -c 'echo $$'` so parallel sessions get distinct paths:
   ```bash
   R=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
   W=$R/.claude/worktrees/t$ID-<pid>
   git worktree add "$W" -b t$ID-short-description origin/main
   python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$W"
   git worktree lock --reason "hunt t$ID (pid <owner-pid>)" "$W"
   cd "$W"
   ```
   Plain `git` works from any checkout of the repo: every worktree shares one
   git store. The `cd` keeps a bare command off the primary checkout.
   If the branch already exists (re-hunt, second session), drop `-b` and name
   it: `git worktree add "$W" <branch>`. Without `origin/main`, use `main`.
   For `<owner-pid>` (use `$PPID`, not the `bash -c 'echo $$'` child; the pid-1
   namespace case) and the conditions under which `worktree-gc` later reclaims
   a stranded tree, see `references/worktree-lifecycle.md`.
   Work only there: absolute
   paths under it, `git -C <worktree>` for git. Ad hoc orchestrators should not
   hand-type this contract: spawn the hunt headlessly with `claude -p "/hunt <id> inline" --model <token>`.
   Choose the model of each launched worker per launch, from the `route` skill grid
   (`skills/route/SKILL.md`); seats that must be independent follow
   `skills/route/references/decorrelation.md` ("The launch line").
   Use per-command `TMPDIR` settings such as `TMPDIR="$W/.tmp" <command>`;
   do not export TMPDIR for the session; never session-wide export it. `.tmp/` is ignored through common Git
   `info/exclude`, remains owned by the worktree, and is never purged separately.
   Evidence stays outside `.tmp/`; deliverables stay outside `.tmp/` too.
5. **Branch.** In a handed-over worktree, create or checkout the ticket branch (the Worktree step already made it otherwise):
   ```bash
   git switch -c t$ID-short-description
   python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$(git rev-parse --show-toplevel)"
   ```
   Registration is idempotent; run it after branch setup for both newly
   created and handed-over worktrees.
6. **Relevant files.** Read the files listed in **Relevant files**.
7. **Test.** Write the first test from the **Test** section of the ticket.
8. **Fail first.** Run `make check-fast` — confirm the test fails.
9. **Implement.** Announce `[Plan → Execute]`, then implement until the affected test passes — `make check-fast` (or the affected test file alone) is the loop gate. The project's pre-PR gate runs once immediately before the Merge request step opens it — not per edit.
   Do not swap a cached or selected result for the Fail-first confirmation or for the project's declared gates.
10. **Self-gate.** Pre-PR self-gate: run `/verify-adherence <branch>` (the branch created in the Branch step).
    - Clean → proceed to Merge request. Note adherence passed in the merge-request description so `/gaze` can skip the mechanical phase on its next pass (gaze reviews; `/verify-gate` gates).
    - Blockers → decide per blocker:
      - Cheap and mechanical (obvious fix, no design judgement) → fix in place, re-run `make check-fast` and `/verify-adherence`, then proceed only once clean. Up to 3 fix-and-recheck cycles; if still not clean after 3 rounds, escalate.
      - A gate slow enough to hurt is a symptom to name in the handoff; the author decides whether to call `/pulse`.
      - Otherwise → STOP. Do not open the PR. Escalate with the adherence report and the blocker list.
    - Circuit breaker: if `/verify-adherence` itself errors, times out, or returns an unparseable result → ESCALATE. Do not open the PR and do not silently skip the gate.
11. **Merge request.** Rebase onto `origin/main` (`rules/git.md` § Merging), run the project's declared pre-PR gate once, then push the branch with lease, wait for CI and open a merge request. Run it through `python3 "$IDH_ROOT/scripts/raid-gate.py" -- <gate command>` so a raid can observe a live long-running gate. If the project has `.idh-checks.json`, its gate command is the project's scoped entry point (or `python3 "$IDH_ROOT/scripts/scoped-check.py"` from its root); quote `selected:` and `skipped:` in the PR description. A mapped doc-only diff may run fewer targets; Python code, unmapped paths, or a project without a map run the full `make check`.
12. **Review.** Review the merge request, unless its tier is bookkeeping
    (`skills/merge/SKILL.md` § Gating tiers): a bookkeeping-only request is
    gated by its mechanical checks alone, so skip Review, Fix and Repeat. Otherwise this action
    is mechanical — invoke the gaze skill with the PR number:
    ```
    Skill(skill: "gaze", args: <pr-number>)
    ```
    Follow the contract the skill loader returns; do not paraphrase or inline its
    steps (mirrors raid Phase 5's mechanical `Skill(hunt)` invocation).
    Each pass through the Review–Fix loop is one **review round**; which
    perspectives run, and how deep, is the reviewer's call
    (`skills/gaze/SKILL.md` § 2–5). What each gaze result leads to (fix and
    review again, close and gate, or stop at the author) is the caller's
    policy in `skills/merge/SKILL.md` § Before merging.
13. **Fix.** Fix all comments regardless of severity. Per fix cycle, run `make check-fast` plus the tests implicated by the comments — not the full suite. If any cycle's fix touches code outside the fast tier, run the full `make check` once, in addition — not on every cycle.
14. **Repeat.** Repeat Review and Fix up to 3 times, i.e. up to round 3. If still not clean, escalate
