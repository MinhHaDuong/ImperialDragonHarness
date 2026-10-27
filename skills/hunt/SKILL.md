---
metadata:
  category: build
name: hunt
description: "Work a ticket: plan, execute in its own worktree, verify and land, wrap up."
disable-model-invocation: false
user-invocable: true
argument-hint: "<ticket-id> [inline]"
---

# Hunt — work ticket $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

A hunt runs four phases: `[Plan]`, `[Execute]`, `[Verify]`, `[Celebrate]`.
Announce each on entry: `[→ Plan]`, `[Plan → Execute]`, `[Execute → Verify]`,
`[Verify → Celebrate]`. The phases are fixed; what runs inside Execute is
not. The plan chooses it, within the ticket's scope and exit criteria.

## Detach

<!-- Fresh subagent to conserve the live session context. -->
Arguments are `<ticket-id> [inline]`; `$ID` is the ticket id.

- Without `inline`, hand the ticket to one background agent with the coder profile
  (`agents/coder.md`) whose first action is
  loading the hunt skill with `$ID inline` as its argument; the prompt holds that and
  nothing more, since the agent loads the phases itself. Report the handoff and end the turn;
  the agent's final report carries any proposal back to the author, a returned monster included.
  Choose the model of each launched worker per launch, from the `route` skill grid
  (`skills/route/SKILL.md`); seats that must be independent follow
  `skills/route/references/decorrelation.md` ("The launch line").
- With `inline` (the detached agent, a raid, a headless run, or the author co-working),
  go on in the current context.

A launcher that wants a wake on silence runs `python3 "$IDH_ROOT/scripts/raid-breaker.py" --wait` in the background (Claude Code only; flags in `skills/raid/references/circuit-breakers.md`). <!-- harness-extension-point -->

## Plan

Read ticket `$ID` (git-erg `tickets/` directory, or the forge) and the files in
its **Relevant files**, then decide what the ticket is and what it takes:

- **Judgment needed**: criteria unclear, a `Label: needs-human` header,
  criteria that decide, arbitrate, sign off or choose, manuscript prose as the
  deliverable, a premise resting on conflicting sources. Settle each by
  `rules/workflow.md` § Escalation protocol (advisor model first) before executing.
- **Already met**: the plan is to record evidence, not to build. Announce
  `[Plan → Execute]`, enter the worktree (§ Worktree), `${ERG:-tickets/erg} log $ID "already met: <evidence>"`,
  commit, skip the rest of Execute, and go to Verify's Prepare to land.
- **Premise expired**: check what changed on **Relevant files** since the
  ticket's `Created` date (`git log --since=<Created> -- <files>`). A change that
  voids the premise is settled by the same escalation protocol; confirmed
  obsolete, log `"obsolete: <commit or change>"` and land as for already met.
  Still valid but worded for an old tree: note it in the plan; the ticket is
  updated on the branch once Execute has entered the worktree.
- **Too big or multipart**: the monster-ticket signals of `rules/workflow.md`
  § Ticket discipline for multi-PR work, or parts that would land in separate
  merges. Do not split it yourself: return it to whoever launched the hunt,
  flagged as a likely monster, with a proposed decomposition (tracker,
  children sized to one sign-off unit, wave order). The caller
  decides: the author approves, reshapes, or says go as one; a raid splits it
  by its own monster checklist and runs the children. Execute only on "go as one".
- **Otherwise**: choose the route. Name the deliverable's kind (code, prose,
  data, configuration, documentation), the work it takes, and the evidence that
  will show each exit criterion met. Code earns tests; prose, data and
  configuration earn the check that fits them (a render, a run, a read of the
  diff), never tests pinning their wording.

Close the phase by announcing the plan in a few lines: the route, why it beats
the obvious alternative, and the evidence Verify will look for. The
announcement informs; proceed without waiting unless a judgment above is
still open.

## Execute

Every route, building or not, starts in the worktree.

### Worktree

Work in the ticket's **own** worktree, on its own branch.

- **Owned already?** Yes if you created it for this ticket, or the spawner
  handed it to you by path with `git status --porcelain` printing nothing:
  there, `W=$(git rev-parse --show-toplevel)` and `git switch -c t$ID-short-description`
  (or switch to the existing branch). A shared or `explore-*` worktree may host a live session: never
  rebase, branch, or leave files in it.
- **Otherwise create one** under the primary checkout. `P=$PPID`, the
  long-lived runtime process, names the path and owns the lock. If `$PPID`
  prints 1 (a sandboxed runtime), use `P=$RANDOM` and the lock reason
  `hunt t$ID (owner pid not visible)` (details: `references/worktree-lifecycle.md`):
  ```bash
  P=$PPID; REASON="hunt t$ID (pid $P)"
  if [ "$P" = 1 ]; then P=$RANDOM; REASON="hunt t$ID (owner pid not visible)"; fi
  R=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
  W=$R/.claude/worktrees/t$ID-$P
  git worktree add "$W" -b t$ID-short-description origin/main
  git worktree lock --reason "$REASON" "$W"
  ```
  If the branch already exists (re-hunt, second session), drop `-b`:
  `git worktree add "$W" <branch>`. Without `origin/main`, use `main`.
- **Register and enter.** `python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" register "$W"`,
  then `cd "$W"`. Work only there: absolute paths under it, `git -C "$W"` for git.
  Scratch files go in `$W/.tmp/`: set `TMPDIR="$W/.tmp"` per command, never for
  the whole session. Evidence and deliverables stay outside `.tmp/`.

### Carry out the plan

For code, test first: write the tests the ticket's **Test** section asks for,
tagged like the project's existing tests (speed tier, Python:
`rules/coding-python.md` § Testing; module, in a modular project); run them by
name and see each fail for the expected reason; implement until they pass,
rerunning them by name as the loop gate. For any other deliverable, do the work
and produce the evidence the plan named.

When the work shows the plan was wrong, replan and announce why; a ticket that
proves to be several goes back up as in Plan.

## Verify

- **Self-gate.** Run the verify-adherence skill on the branch. Fix each mechanical
  blocker in place and run it again, up to 3 times. Escalate instead of landing
  when a blocker needs design judgment, the third run still fails, or the skill
  errors or returns nothing usable.
- **Prepare to land.** Rebase onto the base branch (`<base>`: `origin/main`,
  else `main`; `rules/git.md` § Merging),
  then run the project's fast test tier once (Python: `make check-fast`,
  `rules/coding-python.md` § Testing). The scoped gate (`rules/workflow.md`
  § Check scope) or the full one runs at merge, on the merge candidate.
- **Land by the project's route**, read from its `AGENTS.md` or `CLAUDE.md`,
  never assumed. With a forge: push with lease and open a merge request whose
  description carries the close claim `**Ticket:** tickets/<ticket file>`, then
  wait for CI where it runs on the branch; `/merge` closes the claimed ticket.
  Without one there is no claim to execute; close it on the branch yourself:
  `${ERG:-tickets/erg} close $ID "<reason>"`, then `${ERG:-tickets/erg} archive $ID || true`,
  stage `tickets/` and commit `ticket($ID): close and archive`. Nothing is pushed.
  Either way the merge itself is the caller's, by the project's recipe.
- **Review.** Skip when
  `python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base <base> --head HEAD`
  exits 0 (bookkeeping). Otherwise, with a forge, load the gaze skill with the
  merge-request number and an intent: `verify <what> because <why>`, the
  ticket's exit criteria by default; what each gaze result leads to, a missing
  or stale `reviewed_head_sha` included, is the caller's policy
  (`skills/raid/SKILL.md` § Phase 6; no result:
  `skills/raid/references/detached-gaze.md` § No result). Without one, reviewer seats on
  `git diff <base>...HEAD`, chosen and scaled by risk
  (`skills/route/references/decorrelation.md`). On findings, fix every one
  whatever its severity, rerun what the fixes affect, then the fast tier, push
  where there is a forge, and review again with a new, narrower intent: verify
  those fixes, because they were the findings. Escalate when the review does,
  or when a pass over the fixes still finds blocking items on them. A clean
  review leaves the branch ready to merge.

## Celebrate

Report what landed or is ready to land: the plan as executed, the evidence per
exit criterion, the branch and merge request if any, and what stayed open. The
merge follows the caller's policy; once it is done, the roar skill wraps up.
