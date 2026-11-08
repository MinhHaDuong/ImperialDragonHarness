# Site practice: CI, the test suite and the doctors

All timings are padme (32 cores, shared with parallel sessions and arena coders).

## Current guidance

- **Gate speed.** `make check` takes `-n N` from `scripts/pytest_workers.py` (CPUs available, clamped 2..24). 2026-10-29 measurement: quiet 30-37 s, field median ~75 s; CPU sharing is a hypothesis, not an isolated cause; `-n 32` no gain over 24. [gate contention][source1]
- **Smart-testing helper retired** (held 38% of the gate); testmon only when the author says. [wall time][source2]
- **Testing doctor** (`/test-doctor`, kit `gate_traces.py`, `gate_profile.py`): author-called, never self-started; probes one at a time (contention corrupts timing); `--project` takes a path. Reruns probe counts only full reruns that came back red: 17 reruns, 24.6 min in 28 days [reruns][source3]; [1541][source4]. Author rulings on guards, kit, wait tickets: [User rulings][source5]. Revisit: `gate_traces.py collect` after ~30 sessions; profile if quiet `make check` > 45 s [triage][source6]
- **CI install.** Forge: `astral-sh/setup-uv` then `uv sync --locked`; `ubuntu-latest` ships no uv/ruff/pytest (2026-10-22; recheck at the 26.04 move). [baseline][source7]
- **Local CI.** `scripts/local-ci.sh` is not `make check` (exits 3 SKIP); `act -j` honours only the last `-j`, drops `.git`, long podman socket paths fake catches. [act][source8]; [1088][source9]
- **run_pool throttle** is `wait -n "${pids[@]}"` (PR 2105): a caller's background job ending during the pool no longer counts as a pool slot. The bare-`wait -n` hypothesis was not reproduced (0/400 idle, 0/3600 loaded); an over-limit race on a 127 return remains. [t1396][source10]
- The new dependency, measurement, language, wrapper, and test-target probes are on-demand doctor diagnostics, outside routine healthchecks and merge gates [diagnostics].
## Hazards
- Flakes with cause not established: pool/kill-group tests (`test_local_ci_parallel`), two `idh` lifecycle tests at 60 s; the gate record keeps test ids, not failure text (a later green closed 1322). [1322][source11]
- The after-merge runner inherits `IDH_SESSION_MODEL`/`IDH_SESSION_RUNTIME` from `raid_land.py --session-model`; an autouse fixture in `tests/conftest.py` deletes both (PR 2097) [leak][source12]. A red on main after merge opens a ticket (1419 was closed by PR #2164; its named cause was caller-reported, not re-isolated) [wrapup][source13].
- A stuck required check (1 h 49 min once): do not block on `--watch`; a forge rollup can be stale after a push. [velocity scan][source14]
- Killed test runs leave `idh-tracked-*` in TMPDIR (~20-25/day), below the ticket floor. A gate-record run is blind to hand-timed runs; in a long session reload a helper's `--help` before a mutating call. Skill-card size counts only once tracked, so a gate can go red after commit [1541][source15]. `close-and-clean.sh:67` names the check from the last printed note — wrong after an untagged `bump` (open `consider:`, 1381) [t1381][source16].
- Snapshotting a target FIFO once hung the test-target probe; lstat file-type recording fixed it. The primary remains outside diagnostic execution [diagnostics].
## Open questions
- Is the forge ruleset still seven required checks, no bypass? Unverified; 1045 closed. Gaze wall time is model turns (~67 s orchestrator, derived); route lever untested. On a project with no declared check set, verify-gate ran pytest twice (head, then trial merge) — cadens PR 63; cadens ticket 0052. [monitoring][source17]

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md); [PR #1245](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md); [1082](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md)
- [Doctors landing](../journal/2026/2026-10-27-harness-doctor-and-project-coherence.md); [1240](../journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md); [rename](../journal/2026/2026-10-27-test-doctor-rename-1228.md); [wall time](../journal/2026/2026-10-27-trace-wall-time-pr1722.md); [yawn](../journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md); [practice](../journal/2026/2026-10-28-doctor-practice-and-catalog-links.md)
[diagnostics]: ../journal/2026/2026-11-07-raid-train-controls.md
- [1419 closure](../../tickets/closed/1419-after-merge-red-39718125e6a6.erg).

[source1]: ../journal/2026/2026-10-29-test-doctor-gate-contention.md
[source2]: ../journal/2026/2026-10-21-pulse-gate-wall-time.md
[source3]: ../journal/2026/2026-10-30-test-doctor-reruns-probe-1367.md
[source4]: ../journal/2026/2026-10-21-pulse-testing-expert-1541.md
[source5]: user-rulings.md
[source6]: ../journal/2026/2026-10-29-harness-doctor-triage.md
[source7]: ../journal/2026/2026-10-30-python-tool-baseline-github-runner.md
[source8]: ../journal/2026/2026-10-06-local-ci-act-equivalence.md
[source9]: ../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md
[source10]: ../journal/2026/2026-10-31-t1396-run-pool-throttle.md
[source11]: ../journal/2026/2026-10-28-after-merge-red-1322-cleared.md
[source12]: ../journal/2026/2026-10-31-t1396-session-identity-leak.md
[source13]: ../journal/2026/2026-11-01-raid-1f0534-wrapup.md
[source14]: ../journal/2026/2026-10-21-velocity-scan-stale-baseline.md
[source15]: ../journal/2026/2026-10-21-pulse-testing-expert-1541.md
[source16]: ../journal/2026/2026-10-31-t1381-result-names-checks.md
[source17]: ../journal/2026/2026-10-31-monitoring-and-data-locations.md

## Fallback
