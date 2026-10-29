# Doc propagation survey, PR 1945, and a killed gaze that blocked the landing

Date: 2026-10-29
Project: ImperialDragonHarness

## Context

The author asked how documentation propagation is ensured (README, INSTALL,
catalog, STATE, ROADMAP, docstrings). A survey of origin/main 78a1acb1 found
one enforced check (skills-catalog drift in the merge gate's `before` set),
STATE's line cap, lair step 10, yawn §11, roar step 6 (one line, no documents
named) and gaze's doc-propagation perspective.

## Events

- Measured on refs/notes/review, 40 gaze reviews from 2026-10-28 to
  2026-10-29: 3 ran a docs seat, 10 a consistency seat. The author deferred
  making the seat mandatory until a longer window.
- ROADMAP.md's three "Current priorities" (1045, 1100, 1099) were all closed;
  the file last changed 2026-10-27.
- PR 1945 (ticket 1333): roar step 6 names contracts and documents,
  `tests/test_root_doc_paths.py` checks that paths and make targets named by
  root docs exist, lair step 10 refreshes ROADMAP facts. Mid-run author
  correction: name what is out of scope and point, never restate another
  skill.
- A first gaze run was stopped with TaskStop to push that correction. It left
  `.claude/worktrees/review-1945` (head 0991f359), which made the next gaze
  ESCALATE as "another gaze running". The worktree was removed by hand.
- The killed run's request `rq-20261029T083821123Z-2a8c` had no
  review-heads ref. `raid_land.py` refused the landing ("review-head … of the
  landing review is missing locally"). `review_notes.py keep-head` restored it
  at the head the request recorded (0991f359); the landing then merged at
  6ca71dbf.
- verify-gate first refused for a missing `repo=` argument, then for a stale
  review after a fix commit, and flagged `Ticket: 1333` as a non-canonical
  claim; the body was rewritten to the path form.
- Attribution capture refused until a writer line was recorded with
  `attribution_record.py --record-writer` after the merge.
- The author then asked whether all checks are incremental and when the global
  organization of docs is audited. Answer: no scheduled global audit; the past
  ones were author-led (2026-09-24 rules coherence audit, 2026-10-19 root-doc
  refresh). Tickets 1334 (harness-doctor weight loss, round 2) and 1335
  (harness-doctor docs visit suggested by lair, blocked by 1334) landed in
  PR 1948.

## References

PR 1945, PR 1948, tickets 1333, 1334, 1335, review rv-20261029-pr-1945-cfb1.
