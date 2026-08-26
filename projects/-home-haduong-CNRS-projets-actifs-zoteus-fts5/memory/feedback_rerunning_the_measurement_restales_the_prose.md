---
name: feedback_rerunning_the_measurement_restales_the_prose
description: "Re-running a benchmark after every review round is a review loop's engine; freeze the artifact and generate the figures instead of copying them"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6510fe0-e9fc-4016-a524-09a7f5866457
  modified: 2026-08-22T07:03:33.706Z
---

A review round finds a defect, you fix it, and you re-run the measurement to be
sure. Each run moves the numbers slightly. Every figure quoted in a ticket, a
status document, a README and a merge-request description is now stale, and the
next round opens with a fresh crop of stale-figure blockers. Fix, re-run,
re-stale, repeat.

zoteus-fts5, 2026-08-22: five `/gaze` rounds on one merge request. Rounds 1-2
found real defects in the deliverable. Rounds 3-5 found defects in the *tooling
written to fix round 3's defects*, and one of those tools corrupted a tracked
ticket. Latency medians moved about 1% per run — 101,2 / 101,4 / 103,3 ms — which
was enough to invalidate six documents each time. The user asked "stuck in
loop?" and was right; the engine was the re-run, not the reviewers.

**Why it is hard to see from inside.** Each individual re-run is defensible: the
code changed, so the measurement should be repeated. The cost is not in any one
decision but in the cycle, and the cycle is only visible from outside it.

**How to apply.**

- **Freeze the artifact once the code under measurement stops changing.** Re-run
  for a change that could alter the result; do not re-run to be reassured. When
  a refactor is meant to be output-neutral, prove it by byte-comparing the
  non-timing blocks of two runs and then stop.
- **Copy figures mechanically, never by hand.** Hand-transcribing one number
  into six documents failed five times in that session; it is a copying problem
  and copying is what a machine is for. A declared map from prose location to
  artifact key path, checked in CI, converts the whole class into a test.
  Reference: `bench/check_figures.py` + `tests/test_check_figures.py`.
- **Reduce the number of copies.** The merge-request description went stale
  twice and is the one document such a checker cannot guard, because it is not
  a file in the repo. Move the figures into the ticket and have the description
  point at it.
- **Count the rounds.** Three rounds where every blocker is in the review
  response rather than the deliverable is the signal to stop, freeze, and land.

Related: [[feedback_agent_reported_numbers_need_artifacts]],
[[feedback_ratio_from_one_operating_point]].
