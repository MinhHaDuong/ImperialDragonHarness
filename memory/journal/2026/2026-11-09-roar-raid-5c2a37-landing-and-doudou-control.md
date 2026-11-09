# Roar: raid 5c2a37 landing (PRs 2346, 2347, 2349) and the doudou /paper control (PR 2352)

Date: 2026-11-09 night, host padme. Main at b28fbdfa when roar started.
Merged, each read back MERGED on the forge: PR 2346 (ticket 1493, merge
4900eb226, head ec131769), PR 2347 (ticket 1494, merge 82d92c9c9, head
32f07125), PR 2349 (ticket 1492, merge b28fbdfaa, head 4160461c), PR 2352
(ticket 1489, merge cfe1a024f, head 3b9342dd). Tickets 1489, 1492, 1493, 1494
are under tickets/closed/.

Context: raid 5c2a37 stopped and handed over in writing. The author typed
"Land 2346 2347 2349"; the interface session landed them with
`scripts/raid_land.py --cleanup`, which removed their worktrees and branches.
PR 2352 is a live inspection-only control of the `/paper` published event on
host doudou (ticket 1489), run by a coder of the interface session.

Events reported by the workers (not re-observed by roar):
- The permission layer refused the landing of gate-APPROVED PRs with the
  reason "Merge Without Review", in the raid's session and in the interface
  session, and refused delegating the harness's sanctioned recovery
  (independent review, then one retry). The merges passed after the author
  typed "Land".
- PR 2348 (ticket 1495) stays open and parked after three other-family
  reviews with findings; a third fix round is reserved to the author by
  `skills/raid/references/fix-and-regate.md`; GPT-6 Astra, asked as advisor,
  also chose to park. The raid's own wrap-up items (reroll tally, timing
  table) never ran.

Observed by roar:
- The ticket 1492 log line "2026-11-09T22:05Z reviewer raid 5c2a37 ..." is
  stamped ahead of the clock: `date -u` read 2026-11-09T22:03Z when roar
  started, after the four merges (latest mergedAt 22:01:54Z).
- `scripts/raid_land.py` `check_head` (line 138-140): `git(cwd, "fetch", "-q",
  "origin")` is a bare `subprocess.run` wrapper (line 58-59), so a failed fetch
  is not seen; the comparison then reads the stale `origin/<branch>` ref.
  Listed by the raid lead as a "consider" point; not reproduced.
- Listed by the raid lead for PR 2349, not reproduced: a non-UTF-8 ticket path
  crashes instead of refusing cleanly. PR 2347: no test covers the origin/HEAD
  only path without a local default branch.
- PR 2352 control (ticket 1489 log, 21:55Z lines): the checklist rows for the
  release subfolder, repository tag, landing metadata, HAL and link check not
  done; six steps missing from `skills/paper/references/published.md`; HAL's
  public record still the preprint version (hal-05570600 version 2 on the
  21:54Z API read). No ticket was filed for these.
- Attribution capture: `attribution_record.py --capture-unit` wrote records
  for PR 2347 and PR 2349 (the latter lists a Codex redteam seat reported as
  `gpt-6.1-sol` and a Claude probe seat as `claude-opus-5-5`, copied from the
  review notes). PR 2346 and PR 2352 printed `not derivable` (no seat in the
  review result; no attribution block) and wrote nothing.

Outcome: session tree `.claude/worktrees/raid-1492-1495-1204925-10897`
(detached, handed over by raid 5c2a37) checked at roar time: porcelain empty,
HEAD an ancestor of origin/main, lock pid 1204925 not running.
