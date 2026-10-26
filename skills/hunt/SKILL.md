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

1. Read the ticket (from git-erg `tickets/` directory or forge).
2. Check the **Exit criteria** section. If unclear, ask the author before writing code.
   - If all exit criteria are **already met** (verify by inspection/grep before writing any code), close the ticket through the **normal branch + PR flow**: steps 4, 5 and 11 — never commit the close on `main`.
     Enter the worktree (step 4) and create the branch (step 5) first, then on that branch run
     `${ERG:-tickets/erg} close $ARGUMENTS already-done`, commit the ticket file
     (`git add -u tickets/ && git commit -m "ticket($ARGUMENTS): close — already-done"`
     — `-u` stages the close edit and any dependent Blocked-by removals, never a
     stray file in the shared `tickets/`), and open the
     merge request (step 11). Skip the test/implement steps (6–10); the merge request lands the close
     via review like any other change. Do not stop with an uncommitted-to-`main` or unpushed close.
3. **Route before you execute.** Only a hunt in the author's live interactive
   session reaches this fork. An already-detached executor, an `inline`
   invocation, and a headless run each skip straight to step 4; raid is not a
   second triage. For why each caller skips, and the `$ARGUMENTS` shape, see
   `references/triage.md`.
   - **Needs-human triage.** Read the ticket for these tells, mostly mechanical: a
     `Label: needs-human` header; exit criteria carrying decision verbs (decide,
     arbitrate, sign-off, choose among); manuscript prose as the deliverable, where
     rules/prose/workpackages.md routes an autonomous change through a PR; a
     premise resting on conflicting sources. On a hit, do not execute and write no
     code. Return ONE batched decision list to the author, each item with a
     recommended default, and end the turn. That return is a success outcome of the
     hunt, not a failure, exactly as the raid drift guard treats a premise objection.
   - **Detach by default.** No tell hit, and the hunt is running in the author's
     interactive session: hand the ticket to ONE background agent, which creates
     its own worktree in step 4. Not a raid — for a single ticket its orchestrator and review panels
     cost more than the ticket returns. Launch it with the coder profile (`agents/coder.md`; choose the model per launch from the
     `route` skill, there is no frontmatter pin). The agent's FIRST action is mechanical:
     ```
     Skill(skill: "hunt", args: "$ARGUMENTS")
     ```
     The launch prompt must NOT paraphrase, summarize, or inline hunt's steps;
     `skills/hunt/SKILL.md` is the single live execution contract and the loader
     supplies it fresh on every run (mirrors raid Phase 5). Instruct the agent to
     push its branch and open a merge request as hunt's flow dictates. Then report
     the handoff. Block on the runner with bounded `agent.wait` slices when the
     author is hands-off or the runtime's notifications cannot wake the parent
     turn; a client interrupt cancels the watch, not the runner — re-attach and
     wait again. Otherwise end the turn and say a prompt retrieves the result:
     the interactive session stays at decision altitude instead of accumulating
     the executor's test dumps, diffs, and review rounds, which measured 5.4x the
     cost of the same contract run detached.
4. Work in the ticket's **own** worktree. A worktree is **owned** when you created
   it for this ticket, or the spawner handed it to you by path with
   `git status --porcelain` printing nothing. A shared or `explore-*` worktree that
   may host a live session is **not owned**: a hunt must never rebase, branch, or
   leave uncommitted files in it (a hunt that inherited an orchestration
   session's worktree once rebased its branch and stranded in-progress test edits). Otherwise create one with plain git under the primary checkout,
   `<pid>` from `bash -c 'echo $$'` so parallel sessions get distinct paths:
   ```bash
   R=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
   W=$R/.claude/worktrees/t$ARGUMENTS-<pid>
   git worktree add "$W" -b t$ARGUMENTS-short-description origin/main
   python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$W"
   git worktree lock --reason "hunt t$ARGUMENTS (pid <owner-pid>)" "$W"
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
   hand-type this contract: spawn the hunt headlessly with `claude -p "/hunt <id>" --model <token>`.
   Choose the model of each launched worker per launch, from the `route` skill grid
   (`skills/route/SKILL.md`); seats that must be independent follow
   `skills/route/references/decorrelation.md` ("The launch line").
   Use per-command `TMPDIR` settings such as `TMPDIR="$W/.tmp" <command>`;
   do not export TMPDIR for the session; never session-wide export it. `.tmp/` is ignored through common Git
   `info/exclude`, remains owned by the worktree, and is never purged separately.
   Evidence stays outside `.tmp/`; deliverables stay outside `.tmp/` too.
5. In a handed-over worktree, create or checkout the ticket branch (step 4 already made it otherwise):
   ```bash
   git switch -c t$ARGUMENTS-short-description
   python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$(git rev-parse --show-toplevel)"
   ```
   Registration is idempotent; run it after branch setup for both newly
   created and handed-over worktrees.
6. Read the files listed in **Relevant files**.
7. Write the first test from the **Test** section of the ticket.
8. Run `make check-fast` — confirm the test fails.
9. Announce `[Plan → Execute]`, then implement until the affected test passes — `make check-fast` (or the affected test file alone) is the loop gate. The project's pre-PR gate runs once immediately before step 11 opens the merge request — not per edit.
   Do not swap a cached or selected result for step 8's failing-test confirmation or for the project's declared gates.
10. Pre-PR self-gate: run `/verify-adherence <branch>` (the branch created in step 5).
    - Clean → proceed to step 11. Note adherence passed in the merge-request description so `/gaze` can skip the mechanical phase on its next pass (gaze reviews; `/verify-gate` gates).
    - Blockers → decide per blocker:
      - Cheap and mechanical (obvious fix, no design judgement) → fix in place, re-run `make check-fast` and `/verify-adherence`, then proceed only once clean. Up to 3 fix-and-recheck cycles; if still not clean after 3 rounds, escalate.
      - A gate slow enough to hurt is a symptom to name in the handoff; the author decides whether to call `/pulse`.
      - Otherwise → STOP. Do not open the PR. Escalate with the adherence report and the blocker list.
    - Circuit breaker: if `/verify-adherence` itself errors, times out, or returns an unparseable result → ESCALATE. Do not open the PR and do not silently skip the gate.
11. Rebase onto `origin/main` (`rules/git.md` § Merging), run the project's declared pre-PR gate once, then push the branch with lease, wait for CI and open a merge request. Run it through `python3 "$IDH_ROOT/scripts/raid-gate.py" -- <gate command>` so a raid can observe a live long-running gate. If the project has `.idh-checks.json`, its gate command is the project's scoped entry point (or `python3 "$IDH_ROOT/scripts/scoped-check.py"` from its root); quote `selected:` and `skipped:` in the PR description. A mapped doc-only diff may run fewer targets; Python code, unmapped paths, or a project without a map run the full `make check`.
12. Review the merge request, unless its tier is bookkeeping
    (`skills/merge/SKILL.md` § Gating tiers): a bookkeeping-only request is
    gated by its mechanical checks alone, so skip 12–14. Otherwise this action
    is mechanical — invoke the gaze skill with the PR number:
    ```
    Skill(skill: "gaze", args: <pr-number>)
    ```
    Follow the contract the skill loader returns; do not paraphrase or inline its
    steps (mirrors raid Phase 5's mechanical `Skill(hunt)` invocation).
    Each pass through the 12–13 loop is one **review round**; which
    perspectives run, and how deep, is the reviewer's call
    (`skills/gaze/SKILL.md` § 2–5). What each gaze result leads to (fix and
    review again, close and gate, or stop at the author) is the caller's
    policy in `skills/merge/SKILL.md` § Before merging.
13. Fix all comments regardless of severity. Per fix cycle, run `make check-fast` plus the tests implicated by the comments — not the full suite. If any cycle's fix touches code outside the fast tier, run the full `make check` once, in addition — not on every cycle.
14. Repeat 12–13 up to 3 times, i.e. up to round 3. If still not clean, escalate (see workflow rules).
