---
metadata:
  category: build
name: merge
description: "Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI)."
user-invocable: true
argument-hint: "[-C path] [pr-number]"
---

# Merge $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Run:
```bash
"$IDH_ROOT/skills/merge/erg-pr-merge" $ARGUMENTS
```

**Cross-repo prerequisite**: the script operates on the checkout it runs in,
with the PR branch checked out. Point it at a checkout in one of two ways:

- **`-C PATH` (preferred for agents)** — the script cds into `PATH` before any
  git/gh/erg call. The portable invocation is
  `"$IDH_ROOT/skills/merge/erg-pr-merge" -C WORKTREE N`.
  <!-- harness-extension-point -->
  Use the loaded skill's resolved checkout path; runtime permission rules
  must authorize that path explicitly rather than depend on a retired alias.
- **Implicit cwd** — with no `-C`, the script uses the current directory, so the
  caller must `cd <project-path> && git fetch origin` and check out the PR branch
  before the call.

`-C` with a missing or non-directory path fails loudly before any other work.

## Ticket lines in the PR body

The script reads close intent from the PR **body** only — never the title:

- `**Ticket:** tickets/NNNN-...` or `**Ticket:** tickets/closed/NNNN-...`
  (bold or bare `Ticket:`) — a **close claim**: the named ticket is closed and
  archived on merge. An already closed and archived ticket is accepted as a
  clean no-op.
- `Ticket-ref: tickets/NNNN-...` — references a ticket **without closing it**
  (for annotating a deliberately-open ticket).
- `Ticket: NNNN` (short form) — normalized, not refused: when exactly one
  `tickets/NNNN-*.erg` or `tickets/closed/NNNN-*.erg` matches, the script
  rewrites the body to the canonical path on the forge, reads it back, and
  proceeds; zero or several matches fall through to the error below. Only a
  4-digit ID alone after `Ticket:` qualifies — never `NNNN-slug`,
  `NNNN, MMMM` or `#NNNN`.
- `Ticket: none` — the PR closes nothing.
- With no recognised `Ticket` line, the PR closes nothing (same as
  `Ticket: none`); a line the grammar cannot read is not a claim. A
  malformed `Ticket: tickets/...` path errors, as does the unclosed-fence
  case below.
- Ticket lines inside Markdown code fences are examples and are ignored.
  A fence closes only on a run of the opener's character (backtick or tilde)
  at least as long as the opener, so a `~~~` line inside a backtick fence
  stays fenced; the closer carries nothing after the run but whitespace, and
  a backtick opener's info string may not contain a backtick. A closer sits
  at most 3 columns in (for an opener at 3 columns or less) and tabs advance
  to the next multiple of 4. Deviation from CommonMark: container indentation
  is not tracked, so an opener may sit at any column and a fence nested in a
  list item stays a fence, its closer allowed up to 3 columns deeper than the
  opener; a fence-shaped code line indented 4+ columns outside any container
  also opens a fence and can hide what follows. Ticket paths outside fences that cannot be parsed cause an error.
- An **unclosed** fence whose remaining text holds a `Ticket:` or
  `Ticket-ref:` line with a `tickets/` path or a short ID refuses the merge
  and names the line: the claim would otherwise be silently dropped or read
  from fenced text. Close the fence and re-run.
- Title prefixes like `chore(0216):` are subject references — they **never**
  close anything.

## Attribution block warning

The script also parses the PR body's single fenced `attribution` block
(the attribution parser in `--pr-body` mode; design section 4) and prints
`erg-pr-merge: warning: attribution block missing`, `... invalid: <reason>` or
`... unchecked: <cause>` on stderr. It **never refuses** on this: a missing or
invalid block costs the record, not the merge. `unchecked` means the parser
could not run, which is not an all-clear. Surface the warning in your report
and let the author decide whether to complete the block before merging.

Report stdout/stderr verbatim. If the script exits non-zero, stop and show the error, with one exception: on a gated base, exit **2** means the gate record is missing or stale for this head (none yet, a moved base, or the run's own close commit): run the gate on that head, then run the script again (§ Gated base).

A killed or failed `erg-pr-merge` run (non-zero exit after its rebase) can
leave the PR-branch worktree with a stale pre-rebase index: staged diffs that
appear to re-open closed tickets and revert prose. That is not WIP — run
`git reset --hard HEAD` in that worktree before any salvage or gc decision.

## Queueing and waiting

On an **ungated** base, merge is queued via auto-merge at once, **whether or not checks are still running**: the forge gates on the required checks and merges when they pass, so the script neither refuses on pending checks nor waits for them. A **failing** check is still a refusal, before anything is closed or queued. Where auto-merge is disabled the script reads the checks once and merges directly only if every check is done; pending checks there stop it with a pointer to the status command, never a wait. Where the base requires no checks at all, auto-merge has nothing to wait for and the PR merges at once, pending checks included: gate such a base (§ Gated base).

Queued is not merged. To learn the outcome, ask once with
`"$IDH_ROOT/skills/merge/erg-pr-status" [-C WORKTREE] N`: exit 0 merged, 1
failed (a check failed, or the PR closed unmerged), 2 pending, 3 the forge
could not be read. It reads the forge a single time and never waits; **pending
is a normal answer, not an error**.

**Waiting for a queued merge.** The caller waits itself and finishes the chain
itself (raid: the per-PR roar; roar: its merged-branch pre-check and cleanup).
Where the runtime wakes the session when a background command exits, it starts
exactly one background command with a hard time bound of about 25 minutes, which polls this
single-read status command at an interval inside the command and exits as soon
as the status is no longer pending; the runtime wakes the caller on exit, and
the caller continues from the status it reads. Never ask the author to wait or
to re-run later; never a fixed-delay timer (it waits past the event); never an
unbounded or foreground loop. A runtime that cannot wake the session on exit
(it has no background commands, or runs them without waking the model) asks once
at its next step and reports the PR as pending.

A **draft** PR (roar/raid sweeps file bootstrap PRs as draft) is marked ready automatically before merging, gated base or not — invoking `/merge` is explicit intent to merge.

## Gated base: the gate record

A base branch whose tree carries `.merge-gate.json` with `"gate": "on"` is
**gated** (ticket 1156). The declaration is read from the base: the base fixes
whether the gate is on, which checks run and their commands; the code those
commands execute comes from the branch. No file, or an explicit
`"gate": "off"`, is ungated; any other declaration, or a failure to inspect
the base, refuses. On a gated base the script:

1. takes the latest entry of the `refs/notes/gate` note on the **candidate**
   — the `--no-ff` merge of the branch head into the current base tip,
   rebuilt deterministically on any host — as the gate. A failing entry, or one
   for another scope, refuses (exit 1). No entry for this candidate, because
   none was written, the base moved, or a close commit this run made changed
   the candidate, exits **2**: run the gate on the current head, then the
   script again. Closing the ticket on the branch before gating
   (§ Before merging) avoids the last case;
2. does not read, wait for, or stop on forge check conclusions: the record is
   the gate (author direction 2026-10-21: the forge is a host, CI is not a
   gate; forge CI runs on push to main only, ticket 1174). A forge failure is
   printed as information;
3. never uses forge auto-merge: with no required checks its CLI's auto flag
   merges at once, and an armed auto-merge could land a later head the record
   does not cover; one found armed is disarmed first, or the run refuses;
4. merges with the head pinned (`--match-head-commit`) and succeeds only when
   the PR then reads MERGED.

Write the record from the PR branch checkout, after the ticket close commit:

```bash
python3 "$IDH_ROOT/scripts/merge-gate.py" run --base origin/main --head HEAD
```

It builds the candidate, runs the declared checks in a throwaway worktree of
it, appends an entry (result, time, actor, host, revision, command, scope,
versions, one line per check) to the note and pushes `refs/notes/gate`. The
actor uses the attribution vocabulary (`runtime=… · model=… · effort=…`,
`not-stated` when unstated; a person states `runtime=human`), from `--runtime`,
`--model`, `--effort` or `MERGE_GATE_RUNTIME`, `MERGE_GATE_MODEL`,
`MERGE_GATE_EFFORT`; nothing detects or requires an agent runtime. A record
is a traceable statement, not proof. The forge's notes ref is authoritative:
a `--no-push` record lasts only until the next fetch. `merge-gate.py check --base … --head …`
answers 0 pass, 1 fail, 2 missing, 3 could not read.

**Background merge.** The wait is the gate run itself, so the caller starts
one background command that records and merges:
`merge-gate.py run --base origin/<base> --head HEAD && erg-pr-merge -C WORKTREE N`.
Exit 2 from the helper means record again on the new head and repeat, once;
a second exit 2 (the base keeps moving) goes in the report. A re-run adds no
second close. The base may still move in the seconds between the record
check and the forge's merge; the main-update sweep (ticket 1157) notices that
after the fact.

## Before merging

Two prerequisites the caller checks before invoking this script. (Moved here
from `rules/git.md`, which is resident in every session: a recovery procedure
belongs with the command it recovers.)

- **Merge method drifts per repo.** This harness repo disables squash;
  `MERGE_FLAGS` above hardcodes `--merge`. A repo whose branch protection is
  squash-only rejects that flag — a method recorded in a note goes stale, so
  read the repo's actual merge settings rather than trusting a cached one.
  Trust the merge attempt over the flag: branch protection can bounce a method
  the forge API still advertises. On a squash-merged branch, `git cherry`
  shows `-` for every commit but `is-ancestor` is false — that ancestry check
  is `/roar`'s pre-check, and it is what confirms a squash-merge through the
  forge before a branch gets deleted.
- **After `/gaze`, sync before closing the ticket.** `/gaze` (its simplify
  phase) may have pushed fixes from its own review worktree since the caller last
  fetched: `git fetch origin && git merge --ff-only origin/<branch>` first, or a
  stale rebase silently drops them and the close commit lands on the wrong base.
- **Close the ticket on the branch before gating.** Before the round-1
  `/verify-gate`, the caller closes each claimed ticket on the PR branch:
  `erg close <id> "<reason>"`, `erg archive <id>`, `git add -u tickets/`,
  `git add tickets/closed/<file>`, commit, push. The gate then rules a head
  that already contains the close, and `erg-pr-merge` skips a ticket already in
  `tickets/closed/` with a `Closed:` header. The helper still runs
  `git push origin HEAD`, so it pushes nothing only when that three-way
  equality holds (next item); an unpushed local commit would ride along.
- **Merge prerequisite: the gate's verdict is APPROVED and
  the gate's `ruled_tip_sha` equals `git rev-parse origin/<branch>` at merge
  time, read after `git fetch origin`; otherwise re-gate, do not merge.** Only APPROVED on that tip merges. Run the
  gate as `/verify-gate <pr> repo=<this worktree> session=<uuid>` (one session
  per PR, two rounds at most: `/verify-gate` § Gate sessions); a re-gate past
  that budget is ESCALATE to the author, never a third run.
  Immediately before `erg-pr-merge`, run `git fetch origin`, then
  `git rev-parse HEAD` == `git rev-parse origin/<branch>` == the gate's
  `ruled_tip_sha`; any mismatch means sync or re-gate, never merge.
- **A gaze result of ESCALATE (or none accepted) means no gate and no merge:**
  the review never completed, and the PR goes to the author. "Accepted" means a
  result is present and its `reviewed_head_sha` is not stale against the branch
  tip (as in `/raid` Phase 6), judged before the caller adds its own fix and
  ticket-close commits; those commits do not void it.
- **Run the gate on padme when it is reachable.** On a gated base, write the
  record (§ Gated base) on padme, over ssh from another host; when padme is
  unreachable run it where you are: the record names the host.
  `"$IDH_ROOT/scripts/local-ci.sh"` still reproduces every forge job in the
  forge's image, for a check outside the gate's set.

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

## When the script bounces

`erg-pr-merge` bounces in sequence, and each bounce has its own retry — never
blanket-fall back to a plain forge merge. (Moved here from `rules/git.md`,
which is resident in every session: a recovery procedure belongs with the
command it recovers.)

- **"close: no ticket found" on a retry.** If the claimed ticket is absent
  from both `tickets/` and `tickets/closed/`, stop and inspect the branch and
  claim before retrying. An already archived ticket with a `Closed:` header
  is handled automatically: the script skips closing it again.
- **"auto-merge is unavailable and N check(s) are pending".** The close commit
  is already pushed and the script did not wait. Wait on `erg-pr-status` per
  § Waiting for a queued merge; once it reports the checks done and green,
  re-run the script (a re-run after the close commit adds no second close) or
  finish with a direct forge merge.
- **Empty rollup and unavailable requirement inspection.** With a mergeable
  PR and an explicit empty rollup, the script inspects legacy protection and
  effective rules. Known required checks refuse. HTTP 403 (including permission
  or plan restrictions) permits an ordinary merge attempt without `--admin`
  after validating the other endpoint. This delegates unseen requirements to
  the forge's ordinary enforcement, including its configured actor permissions.
  The script adds no bypass. Other API errors, partial response pages,
  unexpected denial bodies, and malformed successful data still refuse.
  If the forge refuses, its error is reported. Once the blocking requirement is
  resolved, re-run `erg-pr-merge N` after the same `git fetch origin` and
  three-way check; an archived closed ticket is skipped, and the retry pushes
  nothing only when that three-way equality holds (under the documented
  exception, the one helper close commit is already on top and the retry adds
  no second).
- **"must run from PR branch" after a fast-forward.** HEAD is detached after
  `merge --ff-only`: `git checkout <branch>`, then retry.
- **Force-push denied, branch already pushed.** Rebasing rewrites the branch's
  SHAs, local diverges from the remote, and the script's own ticket-close
  commit then lands on the local rewrite with its push rejected — leaving the
  ticket closed and archived locally but the close commit unpushed; a re-run
  fails "close: no ticket found". Recovery: check out the origin branch tip
  detached, `git cherry-pick <close-commit>`, fast-forward push, then merge
  directly (raid 234/235, PR #998).

## Dropped close-claim sweep

After a direct forge merge that bypassed this script, verify each `**Ticket:**`
claim immediately: the ticket must be in `tickets/closed/` with a `Closed:`
header. After a merge wave, run the wider sweep from the updated base checkout:

```bash
bash "$IDH_ROOT/skills/roar/check-close-claims.sh" --days 7 --limit 40
```

It reports how many merged PRs it examined, how many close claims it parsed,
and how many it found unhonoured (`DROPPED` or `UNRESOLVED`). A zero finding
count is not an all-clear when zero PRs or zero claims were parsed; check the
window and any unrecognised bodies. The test suite gives this detector a
positive control: a merged PR claiming an open ticket must be named and cause
exit 1. `Ticket-ref:` is excluded. It reads fences with the same tracker as
this script, except that lines of an unclosed fence count as live: such a body
could only have merged by another route, so the audit names its path claims.
Short-ID claims (`Ticket: NNNN`) are not audited; they land in the
unrecognised count.

## Manual chore-close — when a PR merged without this script

First confirm no close commit rode the PR; if one did, the ticket is already
closed and there is nothing to do. `erg close <ID> <reason>` edits the ticket
file but does **not** stage its own edit, so `git add -u tickets/` BEFORE the
`git mv` to `closed/` and the commit — otherwise the commit carries the rename
with the pre-edit blob and silently drops the `Closed:` header (aedist PR #1008;
a 100%-rename, 0-insertion commit is the tell). A later "no ticket found"
bounce here means a review round already closed it — harmless, skip it.

An `erg-pr-merge` mode taking only a PR number was considered for a head branch
owned by another session. It would close on the caller's branch rather than
putting the close commit on the reviewed PR, weakening the current atomic
close-and-merge path. Keep the branch requirement and `-C` form; if the
isolation guard still makes that branch unreachable, use a direct forge merge
with the immediate verification and sweep above, then repair on a separate
branch and PR.

## After the merge lands

The script reads the PR state once after queueing; when it already reads MERGED
it runs `"$IDH_ROOT/scripts/sync-local-main.sh"` on the base branch
(rules/git.md § Local main syncs eagerly) — no manual sync step. Two outputs
still need action:

- "Merge not yet landed" — the usual case when checks were pending. Wait on
  `erg-pr-status` per § Waiting for a queued merge; on exit 0 run
  `"$IDH_ROOT/scripts/sync-local-main.sh"`; on 1 report the failure; still 2
  when the bound expires, report the PR as pending.
- "left untouched" in the sync report — dirty overlap or divergence where the
  base branch is checked out; report it to the caller rather than forcing.

Do not substitute a hand-rolled `merge --ff-only` on the primary checkout:
that advances whatever branch is checked out there.
