---
metadata:
  category: build
  order: 1
name: hunt
description: "Work a ticket: plan, execute in its own worktree, verify adherence, ask /gaze to review, fix and open a merge request. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<ticket-id> [inline]"
---

# Hunt — work ticket $ARGUMENTS

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

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
  nothing more, since the agent loads the phases itself. Report the handoff and end the turn.
  Choose the model of each launched worker per launch, from the `route` skill grid
  (`skills/route/SKILL.md`); seats that must be independent follow
  `skills/route/references/decorrelation.md` ("The launch line").
- With `inline` (the detached agent, a raid, a headless run, or the author co-working),
  go on in the current context.

A launcher that wants a wake on silence arms `python3 "$IDH_ROOT/scripts/raid-breaker.py" --wait` through `python3 "$IDH_ROOT/scripts/runtime.py" wake arm --after 0 --cmd "<that command>"` (flags in `skills/raid/references/circuit-breakers.md`; how to read the answer in `skills/raid/references/sitrep.md` § Wake sources).

## Plan

Read ticket `$ID` (git-erg `tickets/` directory, or the forge) and the files in
its **Relevant files**, then decide what the ticket is and what it takes:

- **Judgment needed**: criteria unclear, a `Label: needs-human` header,
  criteria that decide, arbitrate, sign off or choose, manuscript prose as the
  deliverable, a premise resting on conflicting sources. Settle each by
  `rules/workflow.md` § Escalation protocol (advisor model first) before executing.
- **Already met**: the plan is to record evidence, not to build. Announce
  `[Plan → Execute]`, enter the worktree (§ Worktree), `${ERG:-tickets/erg} log $ID "already met: <evidence>"`,
  commit, skip the rest of Execute, and go to Verify's Rebase, then Prepare to land.
- **Premise expired**: check what changed on **Relevant files** since the
  ticket's `Created` date (`git log --since=<Created> -- <files>`). A change that
  voids the premise is settled by the same escalation protocol; confirmed
  obsolete, log `"obsolete: <commit or change>"` and land as for already met.
  Still valid but worded for an old tree: note it in the plan; the ticket is
  updated on the branch once Execute has entered the worktree.
- **Surprise**: a route its author would not expect (another deliverable
  kind, work beyond **Relevant files**, a dropped or reinterpreted exit
  criterion, anything irreversible or outward-facing) is asked before
  executing, by the same escalation protocol.
- **Too big or multipart** (`rules/workflow.md` § Ticket discipline for
  multi-request work; drafting: `references/decomposition.md`): return it, unsplit, to whoever launched the hunt with a
  proposed decomposition; execute only on "go as one". Found mid-Execute:
  commit the partial branch (push it where there is a forge), name it in the proposal, unlock the
  worktree and leave it for the caller.
- **Otherwise**: choose the route. Name the deliverable's kind (code, prose,
  data, configuration, documentation), the work it takes, and the evidence that
  will show each exit criterion met. Code earns tests; prose, data and
  configuration earn the check that fits them (a render, a run, a read of the
  diff), never tests pinning their wording.

Check for work in flight on **Relevant files**: open merge requests touching
them (the forge's list with files; none without a forge) and locked worktrees
(`git worktree list`). Name any overlap in the plan and coordinate (a merge
request comment, or a session message where the runtime allows); three or
more on one file take a coordination change first (`rules/workflow.md`
§ Delegation).

Close the phase by announcing the plan in a few lines: the route, why it beats
the obvious alternative, and the evidence Verify will look for. The
announcement informs; proceed without waiting unless a judgment above is
still open.

## Execute

Every route, building or not, starts in the worktree.

### Worktree

Work in the ticket's **own** worktree, on its own branch. A session's own
worktree name, phase and opening line: `references/session-start.md`.

- **Owned already?** Yes if you created it in this run, or the spawner's brief
  names its path explicitly and `git status --porcelain` prints nothing:
  there, `W=<that path>` and `git switch -c t$ID-short-description`
  (or switch to the existing branch). The directory your shell starts in is
  not a handed path: a subagent inherits its spawner's cwd. A tree you did not
  create and no brief named is never adopted, clean or not: stop and report it.
  A shared or `explore-*` worktree may host a live session: never
  rebase, branch, or leave files in it.
- **Otherwise create one** under the primary checkout. `$PPID`, the
  long-lived runtime process, owns the lock; a spawner and its subagents
  share it, so `$RANDOM` makes the path yours, redrawn while it exists.
  If `$PPID` prints 1 (a sandboxed runtime), the lock reason is
  `hunt t$ID (owner pid not visible)` (details: `references/worktree-lifecycle.md`).
  The path is not recomputable: note the printed `$W` and use it verbatim.
  ```bash
  P=$PPID; REASON="hunt t$ID (pid $P)"
  if [ "$P" = 1 ]; then REASON="hunt t$ID (owner pid not visible)"; fi
  R=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
  W=$R/.claude/worktrees/t$ID-$P-$RANDOM
  while [ -e "$W" ]; do W=$R/.claude/worktrees/t$ID-$P-$RANDOM; done
  git worktree add "$W" -b t$ID-short-description origin/main &&
    git worktree lock --reason "$REASON" "$W" && echo "$W"
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
name and see each fail for the targeted reason (an AssertionError on the
behaviour, not an import, argument or fixture error), shown in the run output;
implement until they pass, rerunning them by name as the loop gate. For any other deliverable, do the work
and produce the evidence the plan named.

When the work shows the plan was wrong, replan and announce why.

## Verify

- **Rebase** onto the base branch (`<base>`: `origin/main`, else `main`;
  `rules/git.md` § Merging) before any gate.
- **Self-gate.** Run the verify-adherence skill on the branch. Fix each mechanical
  blocker in place and run it again, up to 3 times. Escalate instead of landing
  when a blocker needs design judgment, the third run still fails, or the skill
  errors or returns nothing usable.
  A verdict never obtained (timeout, spawn refused, no return) is never dropped
  silently: the final report carries `adherence: not obtained (<reason>)`, and
  proceeding on `make lint` alone is allowed only with that line.
- **Prepare to land.** Run the project's lint and fast test tier once (Python:
  `make lint` then `make check-fast`, `rules/coding-python.md` § Testing). The
  scoped gate (`rules/workflow.md` § Check scope) or the full one runs at
  merge, on the merge candidate.
- **Land by the project's route**, read from its `AGENTS.md` or `CLAUDE.md`,
  never assumed. With a forge: push with lease and open a merge request whose
  description carries the close claim `**Ticket:** tickets/<ticket file>`, then
  wait for CI where it runs on the branch; the merge skill closes the claimed ticket.
  Without one there is no claim to execute; close it on the branch yourself:
  `${ERG:-tickets/erg} close $ID "<reason>"`, then `${ERG:-tickets/erg} archive $ID || true`,
  stage narrowly as merge's step Close does
  (`git add -u tickets/ && git add tickets/closed/<id>-*.erg`), and commit
  `ticket($ID): close and archive`. Nothing is pushed.
  Either way the merge itself is the caller's, by the project's recipe.
- **Review.** Skip when
  `python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base <base> --head HEAD`
  exits 0 (bookkeeping). Otherwise, with a forge, load the gaze skill with the
  merge-request number and an intent: `verify <what> because <why>`, the
  ticket's exit criteria by default; what each gaze result leads to, a missing
  or stale `reviewed_head_sha` included, is the caller's policy
  (`skills/raid/SKILL.md` § Phase 6; no result:
  `skills/raid/references/detached-gaze.md` § No result). Without one, write
  the request first, `python3 "$IDH_ROOT/scripts/review_notes.py" open --branch <branch>
  --base-ref <base> --why <why> --intent <what>` (`request --review <id>` on later rounds),
  then load gaze with `branch:<branch>` and the same intent; its result is the
  `answer` entry that `review_notes.py coverage <id> HEAD` reads. On findings, fix every one
  whatever its severity, rerun what the fixes affect, then the fast tier, push
  where there is a forge, and review again with a new, narrower intent: verify
  those fixes, because they were the findings. Escalate when the review does,
  or when a pass over the fixes still finds blocking items on them, except
  the one further round `skills/raid/references/fix-and-regate.md` allows for
  findings that carry a reproduction. A clean
  review leaves the branch ready to merge.
  Attribution lives on notes (`skills/merge/references/claims.md` § Line formats): gaze
  records the reviewer lines; when no orchestrator records the writer lines (a raid does),
  record your own once the review exists, locally:
  `python3 "$IDH_ROOT/scripts/attribution_record.py" --record-writer '<line>' --unit pr:<n>|branch:<branch>`.

## Celebrate

Report what landed or is ready to land: the plan as executed, the evidence per
exit criterion, the branch and merge request if any, and what stayed open. The
merge follows the caller's policy; once it is done, the roar skill wraps up.
