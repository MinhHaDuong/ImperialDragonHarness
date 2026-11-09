# 2026-11-09 — raid 632b19 wave 2: untrack projects/ (1480), notes writer fix (1482), tracker 1478 hand-off

Context: after PR #2310 (ticket 1477) merged, the author extended the raid to tickets 1480 and
1478 in autonomy. Wave base 71047b53 (annotation commit on raid-1477-session).

Events:
- 1480 Imagine (sonnet) said "no script edits needed"; the Blind-Spot pass (opus) found that
  `scripts/resident_census.py:171-175` builds the `projects` path from parts, so the literal grep
  missed it and `tests/test_resident_census.py` would have failed the gate (`max([])` once the
  directory is gone). It also found the "harness key already absorbed by memory-v8" claim false
  (`design/memory-v8/source-inventory.md:22,85`); 1481 was told by log line.
- 1480 Execute (sonnet, hunt inline): one commit, 1085 → 0 tracked files, `make check` 3500 passed.
  Its gaze recorded nothing: `review_notes._write` passed the request entry as
  `git notes append -m <line>`, and a request over a 1,085-file diff exceeded the OS argument
  limit (`OSError: [Errno 7] Argument list too long`). Filed 1482; fixed by the raid itself
  (`-F -`, entry on stdin; red test at 300 KB), PR #2313, gaze panel REVIEWED (red team gpt-6-luna),
  gate APPROVED round 1, merged; main c9656bbd.
- Re-gaze of #2312 then hit two non-code stops: the crashed run's `review-2312` tree held the
  liveness lock for its 20-minute window (ESCALATE "another gaze is live"); the next run's
  regression probe created `projects/zz-probe/memory` and removed only the leaf, so the exit
  preflight saw an empty ignored `projects/` and the close recorded ESCALATE on a review whose
  content had no blocking finding. A third run was needed for a REVIEWED record.
- Tracker 1478's padme remainder (search-works-for-zotero #639 verdict and merge, rebase +
  migrate of five of its PRs and DOIfetch #45, clone sweep) could not be launched: the auto-mode
  classifier denied the cross-repository agent twice (team-lead with merge + ssh, then a
  narrowed no-merge no-ssh version). Logged on 1478; left for sessions in those repositories.
- Verify-gate flagged the raid's own ticket annotation commit as scope overflow on #2313;
  the PR body named the three existing tickets instead of minting one.

Decisions recorded: nothing moved from the export into `memory/` (projects own their notes via
memory-v8; the harness key survives in padme's local store and git history); the history-scrub
question goes to the author with its cost, not executed; `memory/.provenance.json` project keys
out of scope.
- Third gaze on #2312: REVIEWED, panel (correctness haiku, red team gpt-6-luna, regression
  script, self); the seat disclosed that a mid-run `worktree-exit-preflight.sh --removal` purged
  `.panel/2312` (it is not a dry check) and restored the panel from its transcript. Gate APPROVED
  round 1 on tip da6d9b6d (2m20s); merge 25s; main eed4341a. Three `not derivable` attribution
  warnings: line-range anchors (`file:33-38`) are not accepted as repository-relative anchors.
