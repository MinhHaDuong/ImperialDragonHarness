# Test doctor: the fast tier ran serial and took 29 s

Date: 2026-11-10
Project: ImperialDragonHarness

## Complaint

Lair's survey offered a visit: `make check` 36 runs in 7 days, median 41 s, p90 180 s, 38 min waited. The 2026-10-29 revisit was due too (collect after about 30 sessions; look again if the `make check` median stays above 60 s). The author started the visit from that offer.

## Evidence

All on padme, shared with parallel sessions.

- Traces, `gate_traces.py collect --project /home/haduong/.agents --days 7` (read): 559 foreground gate runs in 428 sessions. `make check` median 41 s (76 s on 2026-10-29), first run of a session 41 s, later runs 43 s. `make check-fast` 21 runs, median 31 s, p90 121 s; `make lint + make check-fast` 29 runs, median 43 s. The fast tier ran in about 66 foreground runs, alone or combined.
- `gate_traces.py reruns --days 7` (read): outcome read for 381 of 559 runs; 5 rerun chains, 0 red again, about 3 min. Rerun syndrome excluded.
- Collection floor, `pytest --collect-only -q` (measured): fast tier 1.96 s (1910 of 3798 collected), adherence tier 1.98 s (189).
- `check-fast` paired, alternating, load 4 to 5 (measured): serial 28.7, 29.6 s; `-n 24` 6.3, 7.2 s. Every run 1908 passed, 2 skipped.
- `lint` paired, load 7 to 9 (measured): serial 8.9, 8.8 s; `-n 24` 8.2, 6.5 s; `-n 8` 9.7 s; `-n 4` 6.9 s. Slowest test 1.5 s (`test_deps_declared`), two setups at 1.4 and 1.3 s.
- Full gate during lair (measured): `make check` 3666 passed, 132 skipped, pytest 34.5 s.
- Why serial: the Makefile said "check-fast and lint are deliberately serial (both sit at the pytest boot+collection floor)", a choice from ticket 1011 (2026-10-02) kept in ticket 1215 and never re-measured as the suite grew.

## Diagnosis

Confidence about 90%: the fast tier outgrew the collection floor (2 s floor, 29 s run) and paid it serially. The same tests already run under `-n 24` in every `make check`, so worker safety is tested daily. `lint` still sits near its floor. Unexplained: a cluster of longest waits near 181 s in coder worktrees (compound commands); the 2026-10-29 contention diagnosis is the prior, not re-tested.

## Options offered and chosen

Offered: A route `check-fast` through `scripts/pytest_workers.py` (about 22 s per run, about 24 min of agent waiting per week, derived: 66 runs x 22 s; odds 90%); B leave as is; C also parallelise `lint` (about 2 s of 8 s, within noise; not recommended). Chosen by the author: A.

## Intervention

Branch `test-doctor-check-fast-workers`: `check-fast` takes the `pytest_workers.py` flag; the Makefile comment now says lint stays serial near its floor. No test moved, marked or changed.

## Verification

`make check-fast` in the branch worktree (measured): 10.7 s on the first run (fresh `.venv`, worker boot), 6.3 s warm; 1908 passed, 2 skipped both times. Meets coding-python.md's "under 10 s" warm. `tests/test_makefile_gates.py` 4 passed.

## Revisit

After about 30 sessions, `gate_traces.py collect --project /home/haduong/.agents --days 7`: `make check-fast` median should sit near 10 s. If a fast-tier test flakes under workers, rerun it at `IDH_TEST_WORKERS=0` before blaming this change. If the 181 s cluster persists, look at those compound commands and host load.
