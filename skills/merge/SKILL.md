---
metadata:
  category: build
name: merge
description: "Land a merge request: close its claimed ticket, check the gate record on a gated base, merge pinned to the reviewed head, read the result back, sync local main."
user-invocable: true
argument-hint: "[pr-number]"
---

# Merge $ARGUMENTS

Run each command yourself, from the merge request's own worktree on its head
branch, and read each exit code on its own line, never the tail of a pipe.

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Close claims, short ids, fences, the attribution warning and the edge-case
index: `references/claims.md`. Read it when the body carries a `Ticket` line
you are unsure of, or a case below sends you there.

## Gating tiers

The tier is read from the diff, never judged:
`python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base origin/<base> --head HEAD`
answers 0 bookkeeping (with `--since`, also `unchanged`), 1 full (an empty
diff included), 3 could not read (treat as full).

| Tier | Gating |
|------|--------|
| bookkeeping | Mechanical checks only: on a gated base, the record; on an ungated base, the repo's CI. No `/gaze`, no `/verify-gate`, no review seat. |
| full | `/gaze`, then `/verify-gate` APPROVED; on a gated base, the record. |

**Two moments, whatever the tier** (ticket 1245, tracker 1226). On a gated
base, `.merge-gate.json` declares the full check set (`"checks"`) and its
cheap subset (`"before"`): ticket validator, guards, catalog drift and
`make lint`, no test suite. *Before the merge*, the record (steps 4 to 6)
runs the before set on the candidate and is what the merge rests on.
*After the merge*, step 9 runs the full set, test suite included, on the
new tip of main; a red there is reported, never reverted (Trust, Verify,
Monitor). A change to the gate itself is therefore fully tested only once
it is on main.

**A `/gaze` record counts only if a seat other than gaze itself ran:** one
with `seats: self-only` (`skills/gaze/references/output.md`) counts as no
record, and gaze runs again, from a session that can launch seats.

**A commit added after approval is gated by the tier of its own diff:**
`merge-gate.py tier --base origin/<base> --head HEAD --since <ruled_tip_sha>`.
Bookkeeping or unchanged: the APPROVED verdict stands, no review or gate
round is spent; on a gated base the record is re-run on the new head. Full:
re-gate.

## Before merging

- **Merge method drifts per repo.** This harness disables squash, so the
  recipe passes `--merge`; a squash-only repo rejects that flag. Read the
  repo's merge settings at merge time, and trust the merge attempt over the
  flag.
- **After `/gaze`, sync before closing the ticket.** `/gaze` makes no commits,
  but a fix cycle or another session may have pushed:
  `git fetch origin && git merge --ff-only origin/<branch>` first, or a stale
  rebase drops those commits and the close commit lands on the wrong base.
- **Close the ticket on the branch before gating.** Close each claimed
  ticket (step 1) before the round-1 `/verify-gate`; step 1 at merge time
  then finds nothing to do. A close commit pushed after the gate is a
  bookkeeping delta: the approval stands. An unpushed local commit would
  ride along, so push first.
- **Merge prerequisite, full tier: the gate's verdict is APPROVED and
  what `origin/<branch>` adds to the gate's `ruled_tip_sha` (read after
  `git fetch origin`) is bookkeeping, an empty delta included (§ Gating
  tiers); otherwise re-gate, do not merge.** A bookkeeping-tier
  request needs no verdict.
  **Head checks, immediately before the merge:** `git fetch origin`, then
  `git rev-parse HEAD` == `git rev-parse origin/<branch>` (a mismatch means
  sync, never merge) and, full tier, `merge-gate.py tier --since <ruled_tip_sha>`
  answers 0 (otherwise re-gate). The record on a gated base
  belongs to that same head.
- **Run the gate record on padme when reachable**, over ssh from another
  host; otherwise where you are.

## The recipe

`N` is the merge request, `<branch>` its head branch, `<base>` its base.

Start the step clock before step 0 and end it after step 8 (`skills/gaze/references/output.md`
§ Duration clock). The `duration:` line goes in the report and, always, in a comment
on the request (`gh pr comment N --body "merge <head>: duration: …"`). <!-- harness-extension-point -->

<!-- harness-extension-point -->
Forge commands below use the current forge CLI; another forge needs the same
reads and writes in its own spelling.

0. **Read it, on its branch.** `git rev-parse --abbrev-ref HEAD` must print
   `<branch>`; otherwise stop. Read the request once:
   `gh pr view N --json state,isDraft,headRefName,baseRefName,headRefOid,body` <!-- harness-extension-point -->
   It must be OPEN. Parse the body's close claims (`references/claims.md`)
   and run the attribution check there; its warning never refuses.
1. **Close.** For each claimed ticket not already in `tickets/closed/` with
   a `Closed:` header:
   ```bash
   "${ERG:-tickets/erg}" close <id> "autoclosed — PR #N"
   "${ERG:-tickets/erg}" archive <id> || true  # an erg whose close already archives answers "no ticket found"
   git add -u tickets/ && git add tickets/closed/<id>-*.erg
   ```
   then one commit for all of them, `git commit -m "ticket(<ids>): close and
   archive — PR #N"` with the ids joined by `, `, and `git push origin HEAD`.
   Do not reword that message. A claimed ticket absent from both
   directories: stop, the branch or the claim is wrong. `-u` stages the
   dependents whose `Blocked-by` the close removed, never a stray untracked
   file; the explicit add of the `closed/` path stages the edited blob.
2. **Ready.** A draft request is marked ready: `gh pr ready N` <!-- harness-extension-point -->
3. **Same head.** `git fetch origin`, then the head checks of § Before
   merging. Re-read the body and compare its close claims with the set the
   gate ruled on: a body edited after approval is a stop and a re-gate.
4. **Gate.** `python3 "$IDH_ROOT/scripts/merge-gate.py" enabled --base origin/<base>`
   answers 0 gated, 1 ungated, 3 could not read (stop; never remove the file
   to get through). On a gated base:
   ```bash
   python3 "$IDH_ROOT/scripts/merge-gate.py" check --base origin/<base> --head HEAD
   ```
   0 pass: go on. 2 no record for this candidate (none yet, or the base
   moved): write it with `merge-gate.py run --base origin/<base> --head HEAD`
   from this checkout, then `check` again; re-recording spends no review
   round. 1 fail or stale scope, 3 unreadable: do not merge.
5. **Disarm (gated base only).** Never arm auto-merge: an armed request
   could land a later head than the record covers. Read
   `gh pr view N --json autoMergeRequest -q '.autoMergeRequest != null'`; <!-- harness-extension-point -->
   on `true`, run `gh pr merge N --disable-auto` and read again; still armed: <!-- harness-extension-point -->
   do not merge.
6. **Merge.** Gated base:
   `gh pr merge N --merge --match-head-commit "$(git rev-parse HEAD)"`. <!-- harness-extension-point -->
   Never `--auto`; never `--delete-branch`. Ungated base:
   `gh pr merge N --merge --auto`, or without `--auto` where the repo has <!-- harness-extension-point -->
   auto-merge off and every check is done.
7. **Read back.**
   `gh pr view N --json state,headRefOid,autoMergeRequest -q '"\(.state) \(.headRefOid) \(if .autoMergeRequest then "queued" else "-" end)"'` <!-- harness-extension-point -->
   must read `MERGED <the head of step 3> -`. MERGED at another head is not a
   gated merge: report it. `OPEN … queued` (ungated base): § Waiting for a
   queued merge; `OPEN … -` is not queued. A read that fails or prints
   nothing is unreadable: stop and report, never re-run the merge. The exit
   code of the merge command proves nothing either way.
8. **Sync.** `"$IDH_ROOT/scripts/sync-local-main.sh" . <base>`. A "left
   untouched" line goes in the report, never forced; never a hand-rolled
   `merge --ff-only` on the primary checkout.
9. **After-merge run (gated base).** Start the runner in the background from
   the shared git directory, which outlives this worktree (bare or not), and
   do not wait on it:
   ```bash
   C=$(git rev-parse --path-format=absolute --git-common-dir); mkdir -p "$C/idh"
   (cd "$C" && nohup python3 "$IDH_ROOT/scripts/merge-gate.py" run-after --ref <base> >>"$C/idh/after-merge.log" 2>&1 &)
   ```
   It runs the full set on the newest `<base>` tip and notes the record there
   (a busy lock means a runner already covers this tip). Its red never blocks
   this merge: the log and the note carry it, and `main_sweep.py --after`
   reports it.

## Gated base

A base whose tree carries `.merge-gate.json` with `"gate": "on"` is gated;
steps 4 to 7 and 9 apply. A `--no-push` trial record never admits a merge.

**Background merge.** The wait is the record run, so steps 4 to 8 can run as
one background command. A `check` that answers 2 again after one re-record
(the base keeps moving) goes in the report, not into a loop.

**Waiting for a queued merge.** The caller waits itself and finishes the
chain itself. Step 7's read-back is the single-read status command. Where
the runtime wakes the session when a background command exits, it starts
exactly one background command with a hard time bound of about 25 minutes,
which polls this single-read status command at an interval inside the
command and exits as soon as the status is no longer pending; the runtime
wakes the caller on exit, and the caller continues from the status it reads.
Never ask the author to wait or to re-run later; never a fixed-delay timer
(it waits past the event); never an unbounded or foreground loop. A runtime
that cannot wake the session on exit asks once at its next step and reports
the PR as pending.

```bash
end=$((SECONDS + 1500)); while [ "$SECONDS" -lt "$end" ] && [ "$(gh pr view N --json state,autoMergeRequest -q '.state == "OPEN" and .autoMergeRequest != null')" = true ]; do sleep 60; done  # <!-- harness-extension-point -->
gh pr view N --json state -q .state  # MERGED: sync (step 8); CLOSED: failed; OPEN: still queued at the bound (a failing check leaves auto-merge armed: read the checks) or not queued <!-- harness-extension-point -->
```

## Merge conflict recovery

- **Multi-PR wave on one file: verify the union survived, don't trust a
  clean exit.** Fetch before each sibling merge. A stale `origin/main` ref
  auto-merges cleanly while dropping a sibling's non-conflicting addition:
  no conflict, exit 0, wrong content. Grep the merged file for every
  sibling's marker before committing. On a drop, don't hand-patch: restore
  the known-good base by writing `git show origin/main:<file>` to the path
  (never `git checkout <ref> -- <path>`, which overwrites the index),
  re-layer only this PR's change, re-verify.
- **Conflict inside a *generated* file: regenerate, don't hand-merge.**
  Hand-merging rows mixes one side's text with the other's measurements, so
  resolve the *source*. The reverse trap: regenerating from a stale input
  reverts the other branch's data fix behind a clean merge and a green
  suite. Take `origin/main`'s copy as the base, regenerate to a scratch
  path, and grep the one value the other branch changed. Reproduces →
  commit. Reverts → your input is stale.

## When a step stops

- **Force-push denied, branch already pushed.** A rebase rewrote the branch,
  local diverges from the remote, and the step-1 close commit sits on the
  local rewrite with its push rejected. Check out the origin branch tip
  detached, `git cherry-pick <close-commit>`, fast-forward push, re-gate that
  head.
- **Detached HEAD after `merge --ff-only`.** `git checkout <branch>`, then
  resume at step 0.
- **A merge that skipped step 1** (the web button, another session): verify
  each `**Ticket:**` claim at once; the ticket must be in `tickets/closed/`
  with a `Closed:` header. Repair on a separate branch and merge request
  (`references/claims.md` § Repair). After a merge wave, run the sweep from
  the updated base checkout:
  `bash "$IDH_ROOT/skills/roar/check-close-claims.sh" --days 7 --limit 40`.
