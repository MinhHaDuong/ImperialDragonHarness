# Where gaze spends its wall time (ticket 1197)

Host: padme (64 CPUs). Source: Claude Code session traces of this project, 140 forked `/gaze`
runs from 2026-10-09 to 2026-10-26 (the trace store keeps no older run). Tools:
`scripts/gaze_wall_time.py` (per-run split) and `scripts/gaze_wall_analysis.py` (the tables
below). Labels: READ = a timestamp difference in a trace or a `sar` sample; derived = arithmetic on
READ values, shown. Times are seconds unless a unit follows. Figures drift by a few percent when
rerun, because the live sessions keep adding runs.

## Method and its limits

A run is a `forked-skill` agent named `gaze`. Its wall is last record less first record (READ).
A tool call lasts from its `tool_use` record to its `tool_result` record (READ). A poll is a Bash
call whose command sleeps or loops. A seat is a descendant agent (by `parentAgentId`); its time is
its first to last record (READ). "Model and harness" is the wall less tool time: a residual, so it
also holds waits that end on a background notification instead of a tool result (derived).
Seat time is the seat's own trace, not the artifact's write time, so it can run a few seconds past
the report. Orchestrator model per run is READ from the first assistant record.

Two structures are in the data. Before 2026-10-21 22:00 (112 runs) gaze ran its own gate and fix
phases (37 runs, 88.6 min of gate seats and 72.1 min of fix agents, READ). Since the commits of
that evening gaze runs adherence, the review panel and simplify, makes no commits and runs no gate
(28 runs; 25 with seats). The current structure is the one a fix can act on.

## Criterion 1: per-seat and per-phase durations

All 140 runs: median 287 (4.8 min), p90 820, max 2395 (39.9 min), total 875 min. The ticket's
figures (115 forks, median 4.9, p90 14.1, max 39.9, about 750 min) replicate within the growth of
the sample.

Seat durations in the current structure (READ; median / p90 / max, n):

| Seat | median | p90 | max | n |
|---|---|---|---|---|
| adherence (includes retries) | 37 | 56 | 77 | 54 |
| consistency | 38 | 47 | 65 | 8 |
| correctness | 58 | 176 | 242 | 25 |
| doc-propagation | 50 | 321 | 360 | 11 |
| semantic adherence worker | 50 | 93 | 135 | 15 |
| simplify | 34 | 96 | 142 | 20 |

Before the change the tail was other work: built-in review seats (median 117, max 603), fix agents
(median 211, max 502), gate seats, and one 1010 s review panel seat.

Critical path of the 25 current runs with seats (READ medians; sums are minutes over the 25 runs):

| Segment | median | p90 | sum |
|---|---|---|---|
| run wall | 249 | 460 | 126 |
| setup, before the first seat launches | 49 | 99 | 28 |
| seat span, first launch to last seat end | 127 | 361 | 73 |
| of which the longest single seat | 69 | 290 | 50 |
| of which serial excess (span less longest seat) | 52 | 115 | 24 |
| closing, after the last seat ends | 49 | 115 | 25 |

Setup is 47 s of wall, 6 s of it tools (8 calls median). Closing is 49 s, 6 s of tools (4 calls).
So about 85 percent of both segments is orchestrator model turns (derived: 41/47 and 43/49).
Model time per turn is 3.0 s on Sonnet (126 runs), 3.4 s on Opus (11), 4.8 s on Fable (3), with
median 27, 61 and 52 turns per run (READ).

Wait taxonomy, share of wall (derived from the READ sums):

| Group | wall min | poll | foreground agent | other tools | model and harness |
|---|---|---|---|---|---|
| current structure, 28 runs | 128 | 41% | 4% | 7% | 48% |
| before, 112 runs | 748 | 53% | 0% | 21% | 26% |
| the 12 slowest runs | 255 | 65% | 1% | 10% | 24% |

The 12 slowest runs total 255 min, matching the ticket's 255. Twelve of the slowest 14 runs
contained a gate or fix phase, which gaze no longer runs.

PR 1677, four rounds tonight (READ from the four forks; wall 249, 140, 245, 402 s): seat times
were 30 to 96 s, polls 31 to 81 s. Round 4's own clock says `duration: 6m02s` (362 s); the fork
wall is 402 s because the skill load before the clock starts and the final comment add 40 s
(derived: 402 - 362). Round 4 ran on Opus 5.5 with 54 turns, rounds 1 and 3 on Sonnet 5.5 with
36 and 38 turns. It launched the adherence seat three times (the first artifact was not yaml-fenced)
and waited three times: 81 s for the panel, 41 s for the semantic worker, 51 s for the retry. Those
three waits are 173 s of the 362 s (derived).

## Criterion 2: the three unknowns

**Unknown 1, serial phases versus one slow seat.** Both, and neither is the whole story.
READ: in the current structure the longest seat is 50 of the 73 span minutes and the serial
excess 24; the last seat to finish was simplify in 9 runs, the semantic worker in 8, adherence in 5.
Setup plus closing is 53 of 126 minutes (42 percent), the longest seat 50 (40 percent), the serial
excess 24 (19 percent); the three sum to 127, so the split is exact within rounding. Before the
change the serial gate and fix phases dominated the tail (12 of the slowest 14 runs).
Counterfactual (derived: for each run, the last seat end less the last end of the seats that
remain), dropping simplify from the critical path saves 13 s per run on average, dropping the
semantic worker 12 s, and keeping only adherence, semantic and correctness (a narrow panel) 32 s.

**Unknown 2, do simplify and fix run only on findings.** Simplify does not: it launched in 20 of
the 25 current runs with seats, ending FINDINGS in 13 and REVIEWED in 6 (1 unparsed); it was
skipped in 5, four of them FINDINGS with a blocking adherence verdict, as the skill says. It cost
16.3 min of seat time over 20 runs, and ended the critical path in 9 runs. Fix agents ran in 18
old-structure runs (72 min) and in none of the 28 current runs: gaze no longer fixes.

**Unknown 3, host contention.** Not supported at the tested scope. READ: `sar -q` samples every 10
min on padme from 2026-10-18 give a median 1-minute load of 1.9, p90 20.9, max 95.4 on 64 CPUs.
For 163 adherence seats with a load sample the rank correlation of duration with load is -0.10, and
the median is 39 s below load 20 (158 seats) against 43 s above (5 seats). Over 584 seats of all
kinds, seconds per output token against load is 0.06 (0.011 below load 20, 0.010 above). Positive
control: the same seat durations correlate 0.50 with output tokens, so the join does react to a
real driver. Limits: sysstat starts on 2026-10-18, so the three slowest runs (10-16) have no load
sample; only 5 adherence seats and 34 seats overall ran at load 20 or more; API-side latency is not
visible from the host. A per-run check of the slow tail points the same way: the slow runs on
10-20 and 10-21 had load 1.6 to 11, except 10-20 18:03 (42.9).

**Which of the two competing diagnoses dominates.** Neither. The idle-poll-gap diagnosis (1197,
1216) is refuted as stated: the Bash polls are the orchestrator waiting on running seats, and
they end within 10 s before to 30 s after the nearest seat end in 36 of 43 polls of 20 s or more
(current) and 129 of 183 (before), median signed lag -2.1 and -4.2 s. There is little overshoot to
remove, and a stronger wait primitive (1216) would save seconds here. The wide-panel diagnosis
(1225) is bounded: a narrow panel saves at most 32 s per run (13 percent of a 249 s median), and
less after quality is counted. The two largest buckets are the orchestrator's own model turns in
setup and closing (42 percent) and the single slowest seat (40 percent). The first is a build
problem, the second is a seat-content problem (correctness and doc-propagation p90 are 176 and 321).

## Criterion 3: priced options

Prices: author-hours (agent implementation plus review), USD (recurring), minutes saved per run
(derived from the medians above, n=25). Probabilities are my estimates; none has been run.

| Option | Saves per run | Author-hours | USD | Odds it holds | Note |
|---|---|---|---|---|---|
| Faster orchestrator model | about 0 on Sonnet runs; 5 of 28 current runs used Opus or Fable | 1 (a route-grid entry) | cheaper per turn | 40% | Model time per turn is 3.0 s on Sonnet, 3.4 s Opus, 4.8 s Fable. The saving is on the turns of the 5 non-Sonnet runs (52 to 61 turns against 27). A Haiku orchestrator is unmeasured and the choice belongs to `route`, not gaze. |
| One-call setup and closing script | about 60 s (derived: 41 s of setup model time x 7/9 turns = 32, plus 43 s of closing x 3/4 = 32, rounded down for overlap) | 3 to 4 | not measured; fewer orchestrator turns | 65% | Setup is 8 tool calls and closing 4, each a model turn. Biggest measured lever. |
| Drop the orchestrator pre-review | under 5 s | 0.5 | negligible | 90% it saves, 10% worth the loss | Pre-launch tools total 6 s; the one duplicate, pytest, ran 14 times in 25 runs for 39 s of tool time and overlaps the seats. In round 4 it ran after the launch. |
| Launch the semantic worker with the panel instead of after adherence | up to 12 s average, 50 s in the 8 runs it ends last | 2 | 0 | 50% | The worker reads the adherence seat's verdict; the dependency may be real. Needs a read of `battery.md` phase 3. |
| Narrow panel (ticket 1225) | at most 32 s | covered by 1225 | tokens, not time | n/a | Judged on quality there, not on time. |

**Recommendation:** the one-call setup and closing script. It attacks the largest measured bucket
that has no quality cost. Order of effect: setup and closing are 42 percent of wall, the script
removes about 60 of the 98 s. The pre-review drop is not worth a ticket: it is already inside
setup. Do not act on a wait primitive for gaze on this evidence; 1216 stands on its other
evidence (arena legs), not on gaze. Pin the gaze orchestrator to Sonnet in `route` if the grid
allows: Opus and Fable orchestrators took 52 to 61 turns against 27 (READ), a confound with PR
difficulty not removed.

Not measured, and the cheapest next measurement: Haiku turn latency for the gaze orchestrator, and
a rerun of the current-structure table once about 100 runs exist (25 is thin).
