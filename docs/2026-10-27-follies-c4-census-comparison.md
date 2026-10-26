# Follies detectors on the arena's Pi sessions, against the stall census (ticket 1217)

Written 2026-10-27. Numbers only, no session text. Detectors: `scripts/trace-friction.py` (`--pi-runs`).
Census: `docs/2026-10-26-rail-stall-census.md` in the arena repo (Haiku classification of stalls of 45 s or more, all cycles).
The detectors were written before this comparison and not tuned to it.

## Method

`python3 scripts/trace-friction.py --pi-runs <dir> --json` over the cycle-4 directories `runs-c4-r1` (20 sessions) and
`runs-c4-r1-f1m` (10 sessions), then over the whole arena (472 sessions, the census population). The census counts only calls of 45 s or more,
so the comparison below filters the same way. `--folly-min-seconds 45` reproduces the folly rows; the stall and wait-regex rows come from a one-off script over the same reader and are not emitted by `trace-friction.py`.
Durations are the Pi `durationMs`, so lower and upper bounds coincide for Pi.

## Cycle 4 alone (30 sessions)

| Quantity (45 s or more) | Detector, c4 |
|---|---:|
| Bash calls | 60, 11,433 s |
| Wait-regex calls | 27, 4,643 s |
| Self-matching `pgrep` | 2, 902 s |
| Sleep loop that ran to its cap | 2, 902 s |

The census does not split by cycle.

Without the 45 s filter the c4 legs hold 3 self-matching `pgrep` calls (902 s, one session) and 2 cap-running sleep loops (the same 902 s).
The 902 s is the leg named in ticket 1216. The first c4 directory holds no folly at all.

## All cycles (472 sessions), 45 s or more

| Quantity | Detector | Census |
|---|---:|---:|
| Stalls (Bash only) | 589, 123,192 s | 586, 122,954 s |
| Self-matching `pgrep` | 11, 4,242 s | 10, 4,147 s (11 and 4,267 s in the rail table) |
| Wait-regex calls | 198, 32,583 s | sleep-poll regex 179, 31,058 s (Haiku-classified 161, 26,151 s) |
| Sleep loop to its cap | 7, 3,308 s | no equivalent category |
| Identical failing command repeated in a row | 0 | repeated suite: 32 by regex, 79 by Haiku (a different thing, see below) |

## Reading

- The stall population reproduces within about 0.5 % (589 against 586 calls), so the reader sees the same sessions as the census.
- The `pgrep` detector agrees with the census on count and seconds (11 against 10 to 11; 4,242 s against 4,147 to 4,267 s), by a test that compiles
  the pattern against the command's own text, independent of the census regex.
- The tightened wait regex finds 198 calls against the census regex's 179 and the Haiku classification's 161. It still counts a poll that is
  not on the agent's own job; the three figures are three definitions, not one measured quantity.
- Sleep-to-cap is narrower than "sleep poll": 7 loops that ran to their own cap, out of 161 to 198 polls. Most polls ended on their condition.
- `repeat_failing` finds none at 45 s or more, and the census's repeated suite is a suite re-run, usually after an edit and often passing: another folly,
  not detected here. Whether it needs a detector is the census's open question, not this ticket's.
- Limits: Pi `durationMs` is the runtime's own measure, but the traces record no job end, so no figure here is "hours given back". The stall and wait rows
  at 45 s are not reproducible from the script alone.
