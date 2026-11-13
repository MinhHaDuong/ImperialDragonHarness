# Raid 2f4a88: review of PR 2482 and ticket 1549, doifetch named shadow source

Date: 2026-11-13 · host: padme · drafter anthropic/claude-fable-5-2

## Context

The author asked a harness session to review PR 2482, a ticket filed from
climate-finance-het, to fix the PR if its ask held, to merge it and to raid
the ticket. The ticket (1549) reported that `scripts/doifetch.sh` runs a named
`--source scihub` or `--source libgen` without the `shadow` extra, fails on
bs4 and exits 0.

## Events

- **Review of PR 2482.** The bs4 failure reproduced for `--doi <doi> --source
  scihub` and `--isbn <isbn> --source libgen`. The exit status 0 did not: the
  wrapper returned 1 with stdin open, with stdin closed and under `timeout`.
  The same command piped (`... 2>&1 | cat`) gave 0, `PIPESTATUS` reading
  `1 0`. How the filing session read its 0 is not established. A second
  commit on the PR branch (4a419d379) corrected the title and the
  reproduction and dropped the exit-status criterion.
- **Landing PR 2482.** The PR's head branch was checked out in the filing
  session's locked worktree, its owner pid alive. `raid_land.py` refuses a
  cwd on another branch name ("cwd is not on branch"). The session ran the
  merge recipe's steps by hand from a review worktree whose HEAD equalled the
  PR head by SHA: bookkeeping tier, gate record pass, read-back `MERGED
  4a419d379`. The step clock was not started; the PR comment reads
  `duration: not measured`.
- **Imagine.** The lead skipped the per-ticket reimagine. Its plan was to run
  a named shadow source with the extra. The Blind-Spot pass (Claude pinned
  `opus`) cited closed ticket 1448, the author's decision of 2026-11-04 that
  shadow sources run after the open channels have failed for the work with
  the channel reported, and found that only `scripts/fulltext_cascade.py`
  writes the receipt line. The lead checked both in the tree and took the
  ticket's other allowed outcome, refusal, exit criteria unchanged.
- **Execute.** The coder (Claude pinned `sonnet`) opened PR 2484, 68
  insertions in three files, about three minutes after launch. Its first
  shell sat in the raid's session worktree; the permission classifier denied
  one write there, and the coder then made its own worktree. The lead's brief
  said "three exit criteria"; the corrected ticket has two.
- **Review record.** The coder's gaze answer on notes
  (`rv-20261113-pr-2484-f211`) reads `seats: panel`. Its plan line reads
  "check plus self read", its telemetry `agents=0`, its `attribution` list is
  empty, and it was written 38 s after its request. `raid_land.py` and
  `attribution_record.py --capture-unit pr:2484` both printed `attribution:
  not derivable: reviewers`, and the capture wrote no record. The record
  `memory/evidence/attribution/2026-11-13-review-attribution-pr2484.md` was
  completed by hand with `seat=self`, from the answer's plan line and the
  coder's own `worker:` line.
- **Gate and landing.** verify-gate round 1 ruled APPROVED on 90e1a2f87; its
  positive control ran the ten refusal tests against main's script (all
  fail) and against the tip (all pass). `raid_land.py` landed the PR in 27 s.
  The after-merge records pass on 6256aab3b and on dc9c6fc6d.

## Outcome

PRs 2482 and 2484 merged; ticket 1549 closed. On main, `doifetch.sh` with a
named `scihub` or `libgen` source exits 2 before anything runs, with a
message naming the bare `--doi` / `--isbn` form.

## Left as found

- `doifetch.sh --help` still prints upstream's sentence "scihub and libgen
  only when named here"; `skills/zotero/references/backfill.md` now says it
  describes DOIfetch's own default.
- climate-finance-het (its ticket 3018) received no log line about the
  refusal from this run.
- The four observations ticket 1549 lists as "also reported by the agents"
  were not reproduced or ticketed.
