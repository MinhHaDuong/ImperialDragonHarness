# Site practice: CI, the test suite and the doctors

## Current guidance

All timings are padme (32 cores, shared with parallel sessions and arena coders).

- **Gate speed.** `make check` takes its `-n N` from `scripts/pytest_workers.py` (CPUs available, clamped to 2..24). Suite: 3041 tests; quiet host 30-37 s, field median ~75 s (7 days, p90 101 s). Likely cause: CPU sharing (80%, a diagnosis, not proven). `-n 32` gave no gain over 24 in ten paired trials; `-n 12` is slower under load. [gate contention](../journal/2026/2026-10-29-test-doctor-gate-contention.md)
- **Smart-testing helper retired** (it held 38% of the gate); testmon is revisited only when the author says. [gate wall time](../journal/2026/2026-10-21-pulse-gate-wall-time.md)
- **Testing doctor** (`/test-doctor`, kit `gate_traces.py`, `gate_profile.py`): author-called, never self-started; runs probes one at a time (contention corrupts timing). `--project` takes a path, not a name. Runner-cache knowledge is on demand, not in agent briefs (author ruling). Reruns probe counts only full reruns that came back red: 17 reruns, 24.6 min in 28 days. [reruns probe](../journal/2026/2026-10-30-test-doctor-reruns-probe-1367.md); [1541](../journal/2026/2026-10-21-pulse-testing-expert-1541.md)
- **Author rulings** on guards, the doctor's kit and wait tickets: [Commission](commission.md); here, post-merge measurements live in the doctor's journal revisit. [kit](../journal/2026/2026-10-28-gate-scope-and-doctor-kit.md)
- **Revisit.** Gate: `gate_traces.py collect` after ~30 sessions; profile if the quiet `make check` exceeds 45 s; if pure calls stay above 60 s with the quiet floor holding, offer `nice` for arena tests or a host semaphore. Gaze: after a change to its orchestration or route; compare model time. Harness-doctor lint: reuse the 2026-10-29 dismissals; recheck the `IDH_ROOT` seam count after a Claude Code upgrade. [triage](../journal/2026/2026-10-29-harness-doctor-triage.md)
- **CI install.** The forge installs uv by `astral-sh/setup-uv`, then `uv sync --locked`; `ubuntu-latest` ships no uv, ruff or pytest (as of 2026-10-22; recheck at the 26.04 move). [baseline](../journal/2026/2026-10-30-python-tool-baseline-github-runner.md)
- **Local CI.** `scripts/local-ci.sh` is not `make check`; it exits 3 with SKIP where no workflow is committed. `act -j` honours only the last `-j`; act drops `.git`; a podman socket path over ~108 bytes fakes catches. [act](../journal/2026/2026-10-06-local-ci-act-equivalence.md); [1088](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md)

## Hazards

- Flakes with cause not established: pool and kill-group tests (`test_local_ci_parallel`), two `idh` lifecycle tests at a 60 s timeout. The gate record keeps test ids, not failure text; a later green record closed ticket 1322. [1322](../journal/2026/2026-10-28-after-merge-red-1322-cleared.md)
- A stuck required check (1 h 49 min once): do not block on `--watch`. A forge rollup can be stale after a push. [velocity scan](../journal/2026/2026-10-21-velocity-scan-stale-baseline.md)
- Killed test runs leave `idh-tracked-*` in TMPDIR (~20-25/day); below the ticket floor; sweep at session start if it matters.
- A gate-record run is blind to hand-timed `/usr/bin/time` runs. Reload a helper's `--help` before using it from memory in a long session.
- Skill-card size counts only once the card is tracked, so a gate can go red after commit. [1541](../journal/2026/2026-10-21-pulse-testing-expert-1541.md)

## Open questions

- Is the forge ruleset still seven required checks, with no bypass (author: "I would rather wait than bypass")? Unverified; ticket 1045 is closed.
- Gaze wall time is model turns (~67 s orchestrator per run, derived); the route lever is untested.
- Ticket 1227 delivered ~2 s of the ~60 s priced (judged a miss, 2026-10-29); no follow-up is recorded.

## Retired

- Suite economics of 2026-10-02 (81 s to 33 s) and counts 1514-1627: superseded by the 2026-10-29 measurements.
- GitHub runner guard flip (PR #1133), 1015 closure: fixed, no live consequence.
- `erg-pr-merge`/`erg-pr-status` waits (1082): helper deleted (ticket 1178).
- Ticket 1045 open: closed. Read-back census, 1090 remeasure, raid counts: belong to the merge and wrap-up pages.
- Seam F1 (directory vs path): hunt text now accepts either.
- Tracker 1229 and trace wall-time PR #1722 attribution friction: other departments.

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md); [PR #1245](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md); [1082](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md)
- [Doctors landing](../journal/2026/2026-10-27-harness-doctor-and-project-coherence.md); [1240](../journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md); [rename](../journal/2026/2026-10-27-test-doctor-rename-1228.md); [wall time](../journal/2026/2026-10-27-trace-wall-time-pr1722.md); [yawn](../journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md); [practice](../journal/2026/2026-10-28-doctor-practice-and-catalog-links.md)
