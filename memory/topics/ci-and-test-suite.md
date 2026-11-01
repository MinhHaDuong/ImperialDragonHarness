# Site practice: CI, the test suite and the doctors

All timings are padme (32 cores, shared with parallel sessions and arena coders).

## Current guidance
All timings are padme (32 cores, shared with parallel sessions and arena coders).

- **Gate speed.** `make check` takes `-n N` from `scripts/pytest_workers.py` (CPUs available, clamped 2..24). Suite: 3041 tests; quiet 30-37 s, field median ~75 s; likely cause CPU sharing (a diagnosis, not proven); `-n 32` no gain over 24. [gate contention](../journal/2026/2026-10-29-test-doctor-gate-contention.md)
- **Smart-testing helper retired** (held 38% of the gate); testmon only when the author says. [wall time](../journal/2026/2026-10-21-pulse-gate-wall-time.md)
- **Testing doctor** (`/test-doctor`, kit `gate_traces.py`, `gate_profile.py`): author-called, never self-started; probes one at a time (contention corrupts timing); `--project` takes a path. Reruns probe counts only full reruns that came back red: 17 reruns, 24.6 min in 28 days [reruns](../journal/2026/2026-10-30-test-doctor-reruns-probe-1367.md); [1541](../journal/2026/2026-10-21-pulse-testing-expert-1541.md). Author rulings on guards, kit, wait tickets: [Commission](commission.md). Revisit: `gate_traces.py collect` after ~30 sessions; profile if quiet `make check` > 45 s [triage](../journal/2026/2026-10-29-harness-doctor-triage.md)(../journal/2026/2026-10-29-harness-doctor-triage.md)
- **CI install.** Forge: `astral-sh/setup-uv` then `uv sync --locked`; `ubuntu-latest` ships no uv/ruff/pytest (2026-10-22; recheck at the 26.04 move). [baseline](../journal/2026/2026-10-30-python-tool-baseline-github-runner.md)
- **Local CI.** `scripts/local-ci.sh` is not `make check` (exits 3 SKIP); `act -j` honours only the last `-j`, drops `.git`, long podman socket paths fake catches. [act](../journal/2026/2026-10-06-local-ci-act-equivalence.md); [1088](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md)
- **run_pool throttle** is `wait -n "${pids[@]}"` (PR 2105): a caller's background job ending during the pool no longer counts as a pool slot. The bare-`wait -n` hypothesis was not reproduced (0/400 idle, 0/3600 loaded); an over-limit race on a 127 return remains. [t1396](../journal/2026/2026-10-31-t1396-run-pool-throttle.md)
## Hazards
- Flakes with cause not established: pool/kill-group tests (`test_local_ci_parallel`), two `idh` lifecycle tests at 60 s; the gate record keeps test ids, not failure text (a later green closed 1322). [1322](../journal/2026/2026-10-28-after-merge-red-1322-cleared.md)
- The after-merge runner inherits `IDH_SESSION_MODEL`/`IDH_SESSION_RUNTIME` from `raid_land.py --session-model`; an autouse fixture in `tests/conftest.py` deletes both (PR 2097) [leak](../journal/2026/2026-10-31-t1396-session-identity-leak.md). A red on main after merge opens a ticket (1419; the brief's named cause was caller-reported, not re-isolated) [wrapup](../journal/2026/2026-11-01-raid-1f0534-wrapup.md).
- A stuck required check (1 h 49 min once): do not block on `--watch`; a forge rollup can be stale after a push. [velocity scan](../journal/2026/2026-10-21-velocity-scan-stale-baseline.md)
- Killed test runs leave `idh-tracked-*` in TMPDIR (~20-25/day), below the ticket floor. A gate-record run is blind to hand-timed runs; in a long session reload a helper's `--help` before a mutating call. Skill-card size counts only once tracked, so a gate can go red after commit [1541](../journal/2026/2026-10-21-pulse-testing-expert-1541.md). `close-and-clean.sh:67` names the check from the last printed note — wrong after an untagged `bump` (open `consider:`, 1381) [t1381](../journal/2026/2026-10-31-t1381-result-names-checks.md).
## Open questions
- Is the forge ruleset still seven required checks, no bypass? Unverified; 1045 closed. Gaze wall time is model turns (~67 s orchestrator, derived); route lever untested. On a project with no declared check set, verify-gate ran pytest twice (head, then trial merge) — cadens PR 63; cadens ticket 0052. [monitoring](../journal/2026/2026-10-31-monitoring-and-data-locations.md)
## Retired

- Suite economics of 2026-10-02 (81 s to 33 s) and counts 1514-1627: superseded by the 2026-10-29 measurements.
- GitHub runner guard flip (PR #1133), 1015 closure: fixed, no live consequence.
- `erg-pr-merge`/`erg-pr-status` waits (1082): helper deleted (ticket 1178).
- Ticket 1045 open: closed. Read-back census, 1090 remeasure, raid counts: merge and wrap-up pages.
- Seam F1 (directory vs path): hunt text now accepts either.
- Tracker 1229 and trace wall-time PR #1722 attribution friction: other departments.

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md); [PR #1245](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md); [1082](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md)
- [Doctors landing](../journal/2026/2026-10-27-harness-doctor-and-project-coherence.md); [1240](../journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md); [rename](../journal/2026/2026-10-27-test-doctor-rename-1228.md); [wall time](../journal/2026/2026-10-27-trace-wall-time-pr1722.md); [yawn](../journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md); [practice](../journal/2026/2026-10-28-doctor-practice-and-catalog-links.md)
