---
metadata:
  category: build
name: merge
description: "Merge a pull request with plain commands: close the claimed ticket on its branch, check the gate record on a gated base, merge pinned to that head, read it back, sync local main. A recipe any runtime follows."
user-invocable: true
argument-hint: "[pr-number]"
---

# Merge $ARGUMENTS

A recipe, not a script: you run each command yourself, from the merge
request's own worktree on its head branch, and read each exit code on its
own line, never the tail of a pipe. The safety lives in two retained pieces:
the gate record (`$IDH_ROOT/scripts/merge-gate.py`, declared by the base's
`.merge-gate.json`) and the audit of `main` (`$IDH_ROOT/scripts/main_sweep.py`,
`/lair` step 15). Nothing refuses mechanically on the merge path any more: a
merge without a record is caught afterwards, by the guard hook in enforce mode
and by the audit.

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Close claims, short ids, fences, the attribution warning and the edge-case
checklist live in `references/claims.md`; read it when the body carries a
`Ticket` line you are unsure of, or a case below sends you there.

## Gating tiers

The one home of how much gating a merge needs; `rules/git.md`, `/raid`,
`/hunt` and every `/gaze` caller point here. The tier follows what the diff
touches and is read mechanically, never judged:
`python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base origin/<base> --head HEAD`
prints it and answers 0 bookkeeping (with `--since`, also `unchanged`), 1
full (an empty diff included), 3 could not read (treat as full). The path list is `BOOKKEEPING` in that script: ticket files
(`tickets/*.erg`, `tickets/closed/*.erg`), `STATE.md` and `memory/`; the
ticket tool `tickets/erg` and the ticket docs are not bookkeeping.

| Tier | The diff touches | Gating |
|------|------------------|--------|
| bookkeeping | bookkeeping paths only | Mechanical checks only. On a gated base the record runs the checks `.merge-gate.json` declares under `"tiers"`; this harness declares `validate-tickets` (the ticket check), `agnostic-guard` (lint) and `bookkeeping-tests` (every test that reads tickets, memory or `STATE.md`). On an ungated base, the repo's CI. No `/gaze`, no `/verify-gate`, no review seat. |
| full | anything else: code, rules, skills, config | `/gaze`, then `/verify-gate` APPROVED, seats scaled to the risk (`skills/route/references/decorrelation.md`); on a gated base, the full record. |

**A commit added after approval is gated by the tier of its own diff**, not
by the whole PR's gate again:
`merge-gate.py tier --base origin/<base> --head HEAD --since <ruled_tip_sha>`
diffs the candidate the approval saw against the candidate of the current
head, so it measures only what the head adds. Bookkeeping (a ticket close, a
log line, `STATE.md`, memory) or unchanged (a rebase that leaves the branch's
own change intact): the APPROVED verdict stands, no review round and no gate round are
spent; on a gated base the mechanical record is simply re-run on the new
head. Full: re-gate within the gate session's budget (`/verify-gate` § Gate
sessions), which owns how much of the prior verdict a re-gate reuses.

## Before merging

- **Merge method drifts per repo.** This harness repo disables squash, so the
  recipe passes `--merge`. A repo whose branch protection is squash-only
  rejects that flag — a method recorded in a note goes stale, so read the
  repo's actual merge settings rather than trusting a cached one. Trust the
  merge attempt over the flag: branch protection can bounce a method the forge
  API still advertises. On a squash-merged branch, `git cherry` shows `-` for
  every commit but `is-ancestor` is false — that ancestry check is `/roar`'s
  pre-check, and it is what confirms a squash-merge through the forge before
  a branch gets deleted.
- **After `/gaze`, sync before closing the ticket.** `/gaze` (its simplify
  phase) may have pushed fixes from its own review worktree since the caller last
  fetched: `git fetch origin && git merge --ff-only origin/<branch>` first, or a
  stale rebase silently drops them and the close commit lands on the wrong base.
- **Close the ticket on the branch before gating.** Before the round-1
  `/verify-gate`, close each claimed ticket on the branch (step 1 below), so
  the gate rules a head that already contains the close and step 1 at merge
  time finds nothing to do. A close commit pushed after the gate is a
  bookkeeping delta (§ Gating tiers): the approval stands. An unpushed local
  commit would ride along, so push first and compare `HEAD` with
  `origin/<branch>` (next item).
- **Merge prerequisite, full tier: the gate's verdict is APPROVED and
  what `origin/<branch>` adds to the gate's `ruled_tip_sha` (read after
  `git fetch origin`) is bookkeeping, an empty delta included (§ Gating
  tiers); otherwise re-gate, do not merge.** A bookkeeping-tier request needs
  no verdict: its mechanical checks are the gate. Run the
  gate as `/verify-gate <pr> repo=<this worktree> session=<uuid>` (one session
  per PR, two rounds at most: `/verify-gate` § Gate sessions); a re-gate past
  that budget is ESCALATE to the author, never a third run.
  Immediately before the merge, run `git fetch origin`, then
  `git rev-parse HEAD` == `git rev-parse origin/<branch>` (a mismatch means
  sync, never merge) and, full tier, `merge-gate.py tier --since
  <ruled_tip_sha>` answers 0 (otherwise re-gate). The record on a gated base
  always belongs to that same head.
- **Full tier: a gaze result of ESCALATE (or none accepted) means no gate and no merge:**
  the review never completed, and the PR goes to the author. "Accepted" means a
  result is present and its `reviewed_head_sha` is not stale against the branch
  tip (as in `/raid` Phase 6), judged before the caller adds its own fix and
  ticket-close commits; a bookkeeping delta never voids it (§ Gating tiers).
- **Run the gate record on padme when it is reachable**, over ssh from another
  host; when padme is unreachable run it where you are: the record names the
  host. `"$IDH_ROOT/scripts/local-ci.sh"` still reproduces every forge job in
  the forge's image, for a check outside the gate's set.

## The recipe

`N` is the merge request, `<branch>` its head branch, `<base>` its base.

<!-- harness-extension-point -->
Forge commands below use the current forge CLI; another forge needs the same
reads and writes in its own spelling.

0. **Read it, on its branch.** `git rev-parse --abbrev-ref HEAD` must print
   `<branch>`; otherwise stop. Read the request once:
   `gh pr view N --json state,isDraft,headRefName,baseRefName,headRefOid,body` <!-- harness-extension-point -->
   It must be OPEN. Parse the body's close claims (`references/claims.md`)
   and run the attribution check there; its warning never refuses.
1. **Close (a).** For each claimed ticket that is not already in
   `tickets/closed/` with a `Closed:` header:
   ```bash
   "${ERG:-tickets/erg}" close <id> "autoclosed — PR #N"
   "${ERG:-tickets/erg}" archive <id> || true  # an erg whose close already archives answers "no ticket found"
   git add -u tickets/ && git add tickets/closed/<id>-*.erg
   ```
   then one commit for all of them, `git commit -m "ticket(<ids>): close and
   archive — PR #N"` with the ids joined by `, `, and `git push origin HEAD`.
   That message is the exact text `$IDH_ROOT/scripts/enumerate-merges.py`
   reads to attribute the merge: do not reword it. A claimed ticket absent
   from both directories: stop, the branch or the claim is wrong.
   `-u` stages the dependents whose `Blocked-by` the close removed, never a
   stray untracked file.
2. **Ready.** A draft request is marked ready: `gh pr ready N` <!-- harness-extension-point -->
   Asking for the merge is the intent to merge.
3. **Same head.** `git fetch origin`, then the head checks of § Before
   merging (tier delta since the ruled tip, full tier only). Re-read the body and compare its close claims with the set the
   gate ruled on: a body edited after approval is a stop and a re-gate.
4. **Gate (b).** `python3 "$IDH_ROOT/scripts/merge-gate.py" enabled --base origin/<base>`
   answers 0 gated, 1 ungated, 3 could not read (stop; never remove the file
   to get through). On a gated base:
   ```bash
   python3 "$IDH_ROOT/scripts/merge-gate.py" check --base origin/<base> --head HEAD
   ```
   0 pass: go on. 2 no record for this candidate (none yet, or the base
   moved): write it with `merge-gate.py run --base origin/<base> --head HEAD`
   from this checkout, then `check` again. 1 fail or stale scope, 3 unreadable:
   do not merge. Re-recording after the base moved is mechanical and spends no
   review round: the head, and so the verdict, did not change.
5. **Disarm (gated base only).** Never arm auto-merge: with nothing required it
   merges at once, and an armed request could land a later head than the
   record covers. Read `gh pr view N --json autoMergeRequest -q '.autoMergeRequest != null'`; <!-- harness-extension-point -->
   on `true`, run `gh pr merge N --disable-auto` and read again; still armed: <!-- harness-extension-point -->
   do not merge.
6. **Merge (c).** Gated base:
   `gh pr merge N --merge --match-head-commit "$(git rev-parse HEAD)"`. <!-- harness-extension-point -->
   Never `--auto`; never `--delete-branch` (it fails on the primary checkout's
   lock on `main`; the forge deletes the branch where configured). Ungated
   base: `gh pr merge N --merge --auto`, or without `--auto` where the repo <!-- harness-extension-point -->
   has auto-merge off and every check is done.
7. **Read back (d).**
   `gh pr view N --json state,headRefOid,autoMergeRequest -q '"\(.state) \(.headRefOid) \(if .autoMergeRequest then "queued" else "-" end)"'` <!-- harness-extension-point -->
   must read `MERGED <the head of step 3> -`. MERGED at another head is not a
   gated merge: report it. `OPEN … queued` (ungated base) is
   queued: § Waiting for a queued merge; `OPEN … -` is not queued. A read that
   fails or prints nothing is unreadable: stop and report, never re-run the
   merge. The exit code of the merge command alone proves nothing either way.
8. **Sync.** `"$IDH_ROOT/scripts/sync-local-main.sh" . <base>`. A "left
   untouched" line (dirty overlap or divergence where the base is checked
   out) goes in the report, never forced; never a hand-rolled
   `merge --ff-only` on the primary checkout, which advances whatever branch
   is checked out there.

## Gated base

A base whose tree carries `.merge-gate.json` with `"gate": "on"` is gated;
the declaration is read from the base, the code its checks run
comes from the branch. Steps 4 to 7 apply. `merge-gate.py run` builds the
candidate (the `--no-ff` merge of the head into the base tip, rebuilt
identically on any host), runs the declared checks on it in a throwaway
worktree, and pushes one entry to `refs/notes/gate`; its docstring is the one
home of the record format and the actor fields. A `--no-push` trial record
never admits a merge.

**Background merge.** The wait is the record run, so steps 4 to 8 can run as
one background command. A `check` that answers 2 again after
one re-record (the base keeps moving) goes in the report, not into a loop.
The base may still move in the seconds between `check` and the forge's merge;
the audit of `main` notices that afterwards.

**Waiting for a queued merge.** The caller waits itself and finishes the chain
itself (raid: the per-PR roar; roar: its merged-branch pre-check and cleanup).
Step 7's read-back is the single-read status command.
Where the runtime wakes the session when a background command exits, it starts
exactly one background command with a hard time bound of about 25 minutes, which polls this
single-read status command at an interval inside the command and exits as soon
as the status is no longer pending; the runtime wakes the caller on exit, and
the caller continues from the status it reads. Never ask the author to wait or
to re-run later; never a fixed-delay timer (it waits past the event); never an
unbounded or foreground loop. A runtime that cannot wake the session on exit
(it has no background commands, or runs them without waking the model) asks once
at its next step and reports the PR as pending.

```bash
end=$((SECONDS + 1500)); while [ "$SECONDS" -lt "$end" ] && [ "$(gh pr view N --json state,autoMergeRequest -q '.state == "OPEN" and .autoMergeRequest != null')" = true ]; do sleep 60; done  # <!-- harness-extension-point -->
gh pr view N --json state -q .state  # MERGED: sync (step 8); CLOSED: failed; OPEN: still queued at the bound (a failing check leaves auto-merge armed: read the checks) or not queued <!-- harness-extension-point -->
```

## Merge conflict recovery

- **Multi-PR wave on one file: verify the union survived, don't trust a clean
  exit.** Fetch before each sibling merge. A stale `origin/main` ref produces
  a clean-looking auto-merge that silently drops a sibling's non-conflicting
  addition — no conflict, exit 0, wrong content. "Auto-merging `<file>`" plus
  a clean exit is not proof the union survived: grep the merged file for
  every sibling's marker before committing. On a drop, don't hand-patch —
  restore the known-good base by writing `git show origin/main:<file>` to the
  path (never `git checkout <ref> -- <path>`, which overwrites the index),
  re-layer only this PR's change, re-verify.
- **Conflict inside a *generated* file: regenerate, don't hand-merge.**
  Hand-merging rows mixes one side's text with the other's measurements, so
  resolve the *source*. The subtler trap is the reverse: regenerating from a
  stale input reverts the other branch's data fix while producing a clean
  merge and a green suite, because a generated file carries no marker of
  which input produced it. Take `origin/main`'s copy as the base, regenerate
  to a scratch path, and grep the one value the other branch changed.
  Reproduces → commit. Reverts → your input is stale.

## When a step stops

- **Force-push denied, branch already pushed.** A rebase rewrote the branch,
  local diverges from the remote, and the step-1 close commit lands on the
  local rewrite with its push rejected. Check out the origin branch tip
  detached, `git cherry-pick <close-commit>`, fast-forward push, re-gate that
  head.
- **Detached HEAD after `merge --ff-only`.** `git checkout <branch>`, then
  resume at step 0.
- **A merge that skipped step 1** (the web button, another session): verify
  each `**Ticket:**` claim at once, the ticket must be in `tickets/closed/`
  with a `Closed:` header; repair on a separate branch and merge request
  (`references/claims.md` § Repair). After a merge wave, run the wider sweep
  from the updated base checkout:
  `bash "$IDH_ROOT/skills/roar/check-close-claims.sh" --days 7 --limit 40`.
  A zero finding count is not an all-clear when zero PRs or zero claims were
  parsed.
