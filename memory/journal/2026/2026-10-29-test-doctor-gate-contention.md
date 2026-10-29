# Test doctor: the merge gate stays at 75 s after the 2026-10-21 remedy

Date: 2026-10-29
Project: ImperialDragonHarness

## Complaint

Two revisits were due: the merge gate (2026-10-21 entry, "look again if the `make check` median stays above 60 s") and ticket 1227's criterion 3 (gaze setup and closing after 20 runs). The author chose the gate as what hurts.

## Evidence

All on padme (Threadripper PRO 3975WX, 32 physical cores, 64 threads), shared with parallel harness sessions and arena coders.

- Traces, 7 days, `gate_traces.py collect --project /home/haduong/.agents --days 7` (read): `make check` 148 runs, median 76 s, p90 101 s. After the worker rule of ticket 1215 (2026-10-26 17:32Z): pure `make check` calls (nothing else in the Bash call) 17 runs, median 72 s, range 33 to 106 s.
- Suite size, `--collect-only` (measured): 3041 tests, against 2094 on 2026-10-21 (+45%).
- Quiet-host lab runs (measured 2026-10-29, load 1 to 4 at start): `make check` 35.0 s; in a fresh worktree 37.4 s cold (venv build 0.16 s), 29.7 s warm. Gate steps other than pytest: under 0.1 s each, exit 0.
- Profile, junit, `gate_profile.py profile --workers 24` (measured): serial sum 509.7 s, no test over 10 s, top 10 tests 10% of the total; slowest files `test_zotero_import` 83.5 s, `test_bash_suites` 40.4 s. Lower bound at 24 workers 21.2 s (derived).
- Instrument control (measured): one plain `make check`, 29.1 s inside the command, 32.3 s in the trace. The trace adds about 3 s; it does not explain a 40 s gap. `gate_traces.py` does not unwrap `/usr/bin/time`, so hand-timed runs are invisible to it (below the ticket floor).
- Excluded by the traces (read): first run of a session (79 s against 74 s); overlap with other suite runs of this project (runs with none still median 75 s); load from 10-minute sar samples (slow runs in windows 80 to 99% idle).
- Field log with pytest's own clock (read, `/tmp/chk1299.log`, 2026-10-28 09:03Z): pytest 81.6 s, trace 83 s, host 57% idle in that sar window. The suite itself was slow, not the time around it.
- Contention trial (measured 08:54): with a gaze's full suite (`review-1941`, `-n 24`) and arena coders running, `make check-tests` took 56.7 s; load rose from 31 to 54.
- Workers under live contention, alternating (measured, load 15 to 42): `-n 12` 46.1, 52.3 s; `-n 24` 33.6, 34.4 s. Fewer workers is worse.

## Diagnosis

Confidence about 80%: the gate's suite is healthy (quiet floor about 30 s); the field median of about 75 s is CPU sharing with parallel sessions and arena coders on 32 physical cores. The 2026-10-21 remedy held per test; suite growth absorbed it. Unexplained: a few slow field runs in sar windows near 99% idle (10-minute samples cannot see a 30 s burst).

Gaze revisit (ticket 1227, read, `gaze_wall_analysis.py 2026-10-27T10:45:42Z`): setup median 45 to 39 s, closing 33 to 37 s, whole run 292 to 171 s. The scripts saved little; the run-time drop coincides with ticket 1225 and a shift of orchestrator model (Opus 40 of 180 runs before, 118 of 171 after), so it is not attributable. The ticket's 49 s / 49 s baseline differs from the script's own before-period (45 s / 33 s).

## Options offered and chosen

Offered: A accept; B raise the worker cap 24 to 32 after ten paired trials; C a host-wide gate semaphore; D `nice` for arena coders' tests. Chosen by the author: B, keeping the rule adaptive (doudou: 4 cores, 8 threads).

## Intervention

None to the code. Option B's trials decided against the change. Ten ABBA pairs of `IDH_TEST_WORKERS=24` and `=32`, `make check-tests` (measured, padme, 2026-10-29 09:00 to 09:12 local, load 1 to 43, 0 to 6 other suites running): `-n 24` median 30.1 s, mean 33.5 s, range 28.8 to 55.2 s; `-n 32` median 31.2 s, mean 31.9 s, range 29.3 to 35.2 s. Paired difference (32 minus 24) mean -1.6 s, sd 9.1 s, 32 faster in 4 of 10; the mean rests on one 55 s outlier at 24. The cap stays at 24, in line with ticket 1215's sweep. The rule is already adaptive (CPUs available to the process, clamped to [2, 24]): doudou (8 logical CPUs) gets `-n 8` whatever the cap, so the cap binds only on padme. My trace reads ran during the trials (single-threaded, light).

## Gaze consultation (option B, then G2)

Read from traces, 112 runs since 2026-10-27 10:45Z with setup and closing evidence, `gaze_wall_time.endpoints`: median 178 s = setup 39 s (22% of time) + panel 94 s (57%) + closing 37 s (21%). Panel by seats launched: 1 seat 81 s (n 78), 2 seats 116 s (n 21); by runtime, single-runtime panels claude-code 76 s (n 19), codex 83 s (n 57). Two-seat launches are parallel (11 of 18 in one call, others 3 to 20 s apart); calls after launch total 0 to 7 s, so no poll gaps.

Codex seat sessions (read, `~/.codex/sessions`, 160 sessions with a `review-*` cwd since the cut): wall median 54 s, tool time 1.3 s, model time 53 s; no seat ran the test suite; models `gpt-6.1-sol` 110, `gpt-6-luna` 48. Derived: about 27 s per panel lies between launch and the orchestrator taking the result (81 - 54). Full-suite runs in `review-*` worktrees: 6% of all full-suite time over 3 days (coders' ticket worktrees 48%), so gaze is not a gate-contention source.

Diagnosis: gaze time is model time, orchestrator turns about 67 s per run (derived: 76 s setup and closing less about 9 s of tools) and the seat about 53 s. The levers are fewer orchestrator turns and the route skill's model and effort choice; neither scripts nor polling move it.

Ticket 1227, judged at the author's request: a miss, not a harmful one. Priced at about 60 s per run (65%, 3 to 4 author-hours), delivered about 2 s (setup -6 s, closing +4 s, same endpoints); setup calls 7 to 6, closing 3 to 3. The scripts folded the mechanical calls; the thinking turns (diff read, plan, briefs, plan-check, comment) stayed. The baseline was taken before ticket 1225 rewrote gaze the same morning; the raid premise check asked for a recount of calls on the new text, and none was made. Criterion 3 closed on new endpoints compared with the old 49 s / 49 s. What it left: one-call setup (9 s from start), tested scripts with exit codes, and a correct post-merge cut in `gaze_wall_analysis.py`.

Below the ticket floor: `gate_traces.py` does not unwrap `/usr/bin/time`, so hand-timed runs are invisible to it; a "default" runtime bucket in an ad hoc parse came from launches whose runtime sat in a shell variable.

## Revisit

- Gate: run `gate_traces.py collect --project /home/haduong/.agents --days 7` after about 30 sessions. Profile again (`gate_profile.py`) if the quiet-host `make check` exceeds 45 s (suite growth). If pure `make check` calls stay above 60 s while the quiet floor holds, contention is still the cause: offer `nice` for arena coders' tests (option D) or a host-wide semaphore (C).
- Gaze: revisit after the next change to gaze's orchestration or to the seat or orchestrator route. Measure with `gaze_wall_analysis.py <merge time>` and the Codex seat read above; compare model time, not tool time.
