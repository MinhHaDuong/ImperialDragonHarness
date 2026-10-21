# Testing expert /pulse: from a smart-testing question to a merged consultation skill

Date: 2026-10-21
Project: ImperialDragonHarness

PR [1541](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1541) merged as `6c615565`; ruled tip `745a43e9`; ticket 1159. Review trail: [evidence](../../evidence/2026-10-21-pr1541-review-trail.md); attribution record: `2026-10-21-review-attribution-pr1541.md`.

## Context

The session began as a question: does the harness have smart testing (diff analysis, coverage map, red/green cache)? Reading the repository found three partial mechanisms with no shared key: the testmon helper (`scripts/smart_testing.py`, opt-in, PR 1466), the path-scoped gate selector (`scripts/scoped-check.py`, one confirmed adopter), and the review-evidence reuse record (PR 1521). Only the harness repository wired the testmon helper; two sibling projects had none of it. `rules/coding-python.md` and `skills/hunt` nevertheless instructed agents unconditionally to use it.

## Observations that shaped the decision

- A sibling project's fast tier measured 272 s in its primary checkout with its data present (1596 passed, 81 deselected) and 12.6 s in a throwaway worktree without the data (1199 passed, 750 deselected). Agent traces agreed with the longer figure: 46 foreground runs of the fast-tier target in 80 trace files, median 52 s, p90 228 s, maximum 601 s.
- A second sibling project's recorded durations (dated 2026-07-27, serial) put its fast tier at 15 s over 1122 tests and its slow tiers at about 1000 s, with the top 5 tests holding 50% of the recorded total.
- A sample of the last 300 non-merge commits in three repositories found tests and source changing together in about a third of commits, agents at the same rate or lower than people. Of 25 hand-read commits flagged by a weakening detector, none weakened a test to pass; 24 of 25 flags were benign.
- A delegated read of the two sibling projects' build files found DVC stages with no test stage, tests selected by pytest marker, and most "data-backed" tests reading code or temporary fixtures. Estimates for a hand-built input-keyed cache: 15 author-hours (35% odds) for the larger project and 8 (60%) for the smaller; for declarations under the existing helper, about 2 hours each.
- Session traces carry timestamps on tool calls and results, so command wall time is derivable.

## Decision

The author chose not to instruct agents unconditionally and asked for a testing expert modelled on a doctor's visit, never started automatically, with `/lair` suggesting it from a script that reads speed bumps. The implementation is `skills/pulse/`, `scripts/pulse_traces.py`, `scripts/pulse_profile.py`, `lair` step 13, and removal of the helper instruction from the rule and `hunt` step 8.

## Events during the pull request

- Round 1 of the review panel returned request-changes on one blocker from the only cross-family seat (the survey stayed silent when trace files were unreadable); five of six seats did not block. A fix commit and tests followed; the gate ruled APPROVED.
- Real-data runs of the new survey exposed three defects the synthetic tests had not: a crash when a trace file vanished mid-scan, a stray `)` creating a bogus gate class, and a catch-all label for chained gates.
- The skills channel of the resident-cost census counts every committed skill card against a 6200-character cap with 80 characters of headroom; a card counts only once it is tracked, so the full gate was green before the skill was committed and red after. The card was reduced to 76 characters.
- `main` moved by 26 or more commits while the pull request was open (the gaze stack 1538 to 1540 and others): four rebases, nine full-gate runs and five gate invocations (one of them an ESCALATE for a missing argument).
- PR 1539, merged mid-flight, changed the merge procedure: `/verify-gate` requires `repo=<path>`, a claimed ticket is closed on the branch before the gate, the merged tip must equal the gate's ruled tip, and a pull request gets two gate rounds. Ticket 1159 had not been closed on the branch, and the helper's close commit would have moved the tip after the ruling. The pull request body was changed from a close claim to `Ticket-ref:` and the ticket was closed in the roar bundle.
- `tests/test_local_ci_parallel.py::test_pool_runs_every_item_and_counts_failures` failed in one full-gate run, in a stress run (1 of 36) and on the forge (`'2' == '1'`); cause not established, and a replica of the pool logic did not reproduce it in 2550 trials. PR 1548 replaced the status counting; in a stress run of 120 executions the test failed 3 times on the previous `main` and 0 times on that PR's head.
- `test_kill_groups_reaches_the_whole_group` failed once in a local-CI run of the merge prerequisite (9 jobs passed, 1 failed; 2022 tests passed, 1 failed) and passed 15 of 15 alone and 48 of 48 under contention; it passed in the forge's required check on the same head. Cause not established.

## Outcome

Merged with the forge's required checks green (10 of 10) on the ruled tip. The ticket close, this entry, the attribution record and its evidence file were committed in one wrap-up bundle. Unresolved at wrap-up: the round-1 comment credits a separate `/review` artifact with several findings, and that seat's identity is not in the trail, so it is not in the attribution record.
