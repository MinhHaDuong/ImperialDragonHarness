# Close and clean mechanics

When roar reads this: steps 7, 9 and 10, for what `close-and-clean.sh` checks and reports. The commands stay in roar's SKILL.md.

## Step 7

Exit 0 clean, 1 findings, 2 could-not-look (never an all-clear: a
`tickets/` whose `erg` does not run, an unreadable forge or a failed fetch
all give 2; a repo with no `tickets/` directory at all gets an explicit
`skipped` line for CLOSE and CLAIMS, per the prerequisite policy in the Pre-check section of roar's SKILL.md). Omit
`--ticket` when there is none. Not in a worktree: use `--phase all` with step 10's explicit
cleanup targets and skip step 9. With no targets, cleanup deletes no branches. Its report lines:

- `CLOSE: ALREADY-CLOSED` is the usual case after `/merge`;
  `CLOSED-UNCOMMITTED` means it closed and archived the ticket and you must
  commit that in the wrap-up bundle.
- `CLAIMS`: a PR body's `**Ticket:**` line is executed by the merge recipe's
  close step, not by the forge. Any other route — a bare forge-CLI merge, the forge's
  web UI, another machine, another session — lands the code and drops the
  claim with no output, and `erg check` passes either way. The
  findings are `DROPPED` (ticket exists, no `Closed:` header) or
  `UNRESOLVED` (no such ticket here — renumbered, or this checkout is
  behind). The script never repairs a `DROPPED`: do it with
  `tickets/erg close <id>` plus `tickets/erg archive`, committed like any
  other change. `/yawn` step 9 does not cover this: it indexes on
  the `Closed:` header being *present*, so it is blind to a ticket that was
  never closed at all.

## Step 9a

It runs a fresh preflight (the step-7 result predates the wrap-up
work), the bounded integration fetch, the ancestry check of HEAD, or
for the bundle: its remote tip equals HEAD and its merge request is
open with auto-merge armed or, on a gated base (`.merge-gate.json`), it
reads OPEN with a passing gate record on its candidate merge commit, or
MERGED; a gated bundle not yet MERGED stays pending in step 11. It then syncs local `main`, best effort.
`PREFLIGHT: DIRTY` → commit (or `$IDH_ROOT/scripts/worktree-salvage.sh`)
and re-run; the preflight removes only `.panel/` and `build/panel-head/`
review scratch when no `.tmp/` exists, and refuses every other
uncommitted file, including an uncommitted ticket draft. If `.tmp/` exists, ordinary preflight preserves `.panel/` verdicts
until the citation-aware removal check has run.

## Step 9b

The gate requires merged ancestry and clear, readable citation coverage
across PR bodies, branch commits, and verdicts. A citation, unreadable
source, or uncertain ancestry retains `.tmp/` and the worktree; report
`KEEP-PENDING` with the reason. A clear gate prints `.tmp/` size before
removal. Git refuses a tree with modified or untracked files, and the
branch survives removal, so no commit is lost; ignored files are deleted
with the tree. Never `--force`.

## Step 10

`--local-branch B=OID` and `--remote-branch B=OID` are independent,
repeatable cleanup targets. Omit either side if there is no verified
target there (for example, the forge already deleted the remote branch).
With neither option, the helper deletes nothing. Repeated cleanup reports
already absent targets; remote absence is checked at the named remote ref,
rather than inferred from a missing tracking ref. A squash/rebase merge
whose original head is not an ancestor is retained; patch equivalence
may justify the wrap-up pre-check but does not authorize deletion here.

The helper fetches only the default integration branch into its tracking ref,
ignoring configured refspecs and opportunistic refmaps. It disables tags,
pruning, submodule recursion and automatic maintenance, then resolves exact
refnames, requires the supplied full OID to match, and checks ancestry
against `refs/remotes/origin/<default>` (the local default without origin).
`--default-branch B` overrides the default read from `origin/HEAD`, falling
back to main. Default, current, symbolic and occupied branches remain and are reported
as retained findings (exit 1).
A named completed-PR branch at the integration tip is eligible; ownership
comes from the explicit PR evidence, not its relationship to that tip.

Immediately before local deletion it rechecks the OID and occupancy, then
uses ordinary `git branch -d`, with its remote overridden for that command
to `idh-roar-head-check-<approved-OID>`. Before the override it verifies that
no configuration keys exist for that alias; a configured alias is a retained
finding and an unreadable config is could-not-look. The nonempty unconfigured
alias makes Git check containment in HEAD as an additional conservative guard,
avoiding the empty-remote crash for tracked branches in Git 2.53.
A checkout behind integration may therefore retain an otherwise eligible
target. This retains Git's merge and worktree refusal
without editing persistent upstream config. These prechecks are not atomic
with deletion and do not promise safety against arbitrary concurrent ref
writers. Remote deletion leases the supplied OID. Drift, unmerged targets
and refused deletes are findings (exit 1); unreadable prerequisites are
could-not-look (exit 2), never an all-clear. No delete-and-restore recovery
or human-output parsing is used. Report retained targets for later handling;
do not broaden the cleanup scope.
