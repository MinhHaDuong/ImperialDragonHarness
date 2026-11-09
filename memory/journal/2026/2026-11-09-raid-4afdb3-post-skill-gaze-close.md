# 2026-11-09 — raid 4afdb3: tickets 1486 (/post skill) and 1491 (gaze_close containment crash)

Context: two-ticket raid on padme, author live, launched at 20:50Z after the 1478 and 1485
sessions. Merged: PR #2341 (1491, head b6390739, gate session 6b382e7a) and PR #2342 (1486,
head 4251090b, gate session d78b6035). Raid id 4afdb3; session branch raid-1486-1491-session
landed as PR #2340 before the wave, so WAVE_BASE dcefbc30 carried every annotation.

## Observable events

- Ticket 1491 was not on main when the raid started: it existed as untracked files (ticket and
  claim) in the primary checkout, written by a gaze session at 19:13Z. `erg ready` listed it
  from the working tree. The raid filed it on its branch; the local main sync then refused to
  fast-forward over the untracked copies until they were moved aside.
- Blind-Spot pass (opus) over the two Imagine outputs returned five material omissions, two of
  which changed the 1491 path: the close may run with its cwd inside the removed tree
  (`Path.cwd()` raises before cleanup), and substituting the primary for the gone tree would
  raise a false "differs from entry branch" flag whose documented repair switches main's checkout.
  Both went into the ticket before Plan; the executor implemented both.
- 1486: the carnet and the missions folder are on doudou, not padme. The executor traced both
  dry runs against the real carnet procedure over ssh; the carnet is not a git repository, so the
  one-line pointer to /post was an author act. Gate round 1 ruled REROLL on that line alone; the
  author inserted it with a sed over ssh; round 2 APPROVED on the same session, three minutes.
- Census: the /post card took the tracked skills channel to 6323 of 6300; three description trims
  brought it to 6248. The cap was not raised.
- Merge permission: the auto-mode classifier refused `raid_land.py` for PR #2341 twice and for
  PR #2342 once, each as "Merge Without Review", with gaze REVIEWED and verify-gate APPROVED on
  notes. Each merge then passed on the first try right after the author's message named the
  PR ("Land 2341", "Land 2342"). Bookkeeping landings of the raid's own ticket-only PRs
  (#2340, #2343) passed without that; a ticket-only PR from another session's worktree (#2337)
  was refused and the author landed it by hand.
- The author asked mid-raid for a verify-and-reimagine pass on 1491 to 1495. Four sonnet agents
  reproduced or refuted each premise by command; a Blind-Spot pass (opus) found that the 1495
  pid-type check would reject the raid's own session (a claimed bg-spare keeps its command line
  for life), that the 1492 guard as proposed would block five legitimate file-and-close PRs of the
  last hundred, and that 1494's forge criterion and 1493 on its face sit below the severity floor.
  The record and the author decisions each ticket needs landed as PR #2343; nothing executed.
- The 1486 executor observed `tests/test_review_trajectory.py::test_unreadable_repo_is_not_checked`
  hanging with TMPDIR set inside the worktree, as hunt's recipe says, and passing with the default
  TMPDIR (memory already notes four such tests, 2026-11-09).

## Outcome

Both tickets closed and archived by their merges. Open, the author's: live `/post` dry runs on
doudou; a `/update-publist` row for posts and op-eds and the bibliography path mismatch between
the carnet and that skill; the four wave-2 candidates' decisions; whether `raid_land.py --cleanup`
should refuse a worktree a live process sits in (1491's known remover).

References: raid log raid=4afdb3; reviews rv-20261109-pr-2341-bd15, rv-20261109-pr-2342-c439;
tickets/closed/1486, tickets/closed/1491; tickets 1492-1495 "## Verify and Imagine" sections.
