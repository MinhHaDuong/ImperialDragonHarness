# Pulse: the merge gate takes about 90 s

Date: 2026-10-21
Project: ImperialDragonHarness

## Complaint

The author reported the merge gate at about 90 s, a slow development loop. Already tried: deleting the erg merge helper (ticket 1178, PR 1619).

## Evidence

- Traces, 28 days, `pulse_traces.py collect --project /home/haduong/.agents` (read from a record, 2026-10-21): `make check` 334 foreground runs, median 78 s, p90 201 s, max 601 s, 596 min in total. `make check-fast` median 10 s, `make lint` 6 s. First run of a session 76 s, later runs 90 s. The first two probes returned zero runs because `--project` takes a path, not a name; the probe fired once given the path.
- Gate steps other than pytest, measured on this host (padme, 2026-10-21): about 1.6 s in total.
- `make check-tests`, `-n 4`, junit durations (measured, load 5.9 to 7.4, two other sessions live): 104 s wall, 2157 passed, 4 skipped. Serial sum of durations 269.1 s; lower bound at 4 workers 67 s (derived).
- Per-file: `tests.test_smart_testing` 102.2 s of 269.1 s (38%), 73 tests, each building a throwaway git repo and booting a nested pytest with testmon. No single test above 5.2 s. Next files: `test_zotero_import` 29.8 s, `test_bash_suites` 29.5 s.
- Use of the helper in traces (28 days): no run of `make smart-test`, `make smart-refresh` or `python -m scripts.smart_testing` apart from the probing session itself. This was not the deciding argument: the helper was two days old and the author pointed out that absence of use says nothing about a new tool.

## Diagnosis

Confidence about 70%: the gate is pytest; one helper's own suite holds 38% of its serial time. Contention with parallel agent sessions explains the gap between the 67 s floor and 104 s and the long p90, not proven. Unexplained: the tail beyond 200 s.

## Options offered and chosen

Offered: A share one fixture repo across the 73 tests; B tier the file out of the gate; C raise workers to 8; D do nothing; E retire or slim the helper. Chosen by the author: retire the helper (E) and try 8 workers (C), with testmon left for another day.

## Intervention

Branch `explore-pulse-2723369`: the commit "tests: retire the smart-testing helper; it costs 38% of the gate" retires `scripts/smart_testing.py`, `scripts/smart_testing_inputs.py`, `tests/test_smart_testing.py`, `tests/smart-testing/`, the Makefile targets, the `.gitignore` lines, the `pytest-testmon` pin and lock entry, the smart half of `tests/conftest.py`, the pulse toolkit section and the pulse test that guarded it. 74 tests removed. The commit "make: run the full gate on 8 xdist workers" sets the full gate to `-n 8`.

## Verification

- Serial sum, same suite, junit (`pulse_profile.py compare`): 269.1 s to 164.2 s (-105.0 s); only `tests.test_smart_testing` moved (-102.2 s).
- Workers, three alternating trials each through `uv run --frozen`, load 7 to 9: `-n 4` 48.5, 47.3, 45.0 s (mean 46.9); `-n 8` 33.3, 33.9, 34.1 s (mean 33.8). All six: 2094 passed, 4 skipped.
- A first set of trials with bare `python3` lacked the zotero dependencies (4 import errors, 1839 passed) and is void.
- Wall time 104 s before against 46 s after the removal is not like for like (load 6 to 7 against 2 to 5); only the serial-sum delta and the paired worker trials are.

## Revisit

Run `pulse_traces.py collect` after about 30 sessions. Look again if the `make check` median stays above 60 s. Worker safety at 8 rests on six clean runs; if a pool or kill-group test flakes again, test at `-n 4` before blaming the helper's removal. Testmon: revisit when the author says.
