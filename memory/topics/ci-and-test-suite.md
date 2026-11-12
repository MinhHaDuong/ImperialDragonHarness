# Site practice: CI, the test suite and the doctors

All timings are padme (32 cores, shared with parallel sessions and arena coders).

## Current guidance

- **Gate speed.** `make check` and, since 2026-11-10, `make check-fast` take `-n N` from `scripts/pytest_workers.py` (CPUs available, clamped 2..24); `lint` stays serial near its 2 s collection floor. check-fast went from ~29 s serial to 6-7 s warm (PR 2441). `make check` median 41 s over 7 days (76 s on 2026-10-29); CPU sharing is a hypothesis, not an isolated cause. [visit][source18]; [contention][source1]
- **Smart-testing helper retired** (held 38% of the gate); testmon only when the author says. [wall time][source2]
- **Testing doctor** (`/test-doctor`, kit `gate_traces.py`, `gate_profile.py`): author-called, never self-started; probes one at a time; `--project` takes a path. Reruns probe: 5 chains in 7 days, 0 red again (2026-11-10) [visit][source18]; [reruns][source3]. Revisit after ~30 sessions: check-fast median near 10 s; a fast-tier flake reruns at `IDH_TEST_WORKERS=0` before blaming workers; a ~181 s wait cluster in coder worktrees is unexplained [visit][source18].
- **CI install.** Forge: `astral-sh/setup-uv` then `uv sync --locked`; `ubuntu-latest` ships no uv/ruff/pytest (2026-10-22; recheck at the 26.04 move). [baseline][source7]
- **Local CI.** `scripts/local-ci.sh` is not `make check` (exits 3 SKIP); `act -j` honours only the last `-j`, drops `.git`. `scripts/scoped-check.py` errors here: the harness has no `.idh-checks.json` [act][source8]; [1488][source19]
- **After-merge red.** Read `.git/idh/after-merge.log` (the `tmp_path`/`mktemp` paths) and the runner's `/proc/<pid>/environ` before treating main as broken. The after-merge-red ticket criterion was reworded (PR 2370): no gate can read a post-merge record [false red][source20].
- New dependency, measurement, language, wrapper and test-target probes are on-demand doctor diagnostics, outside routine gates [diagnostics].
## Hazards
- `TMPDIR` inside a worktree (hunt's per-command recipe) fails or hangs five "outside a git repository" tests; they pass with the default `TMPDIR` [1483][source21]. A runner inherited a roar agent's `TMPDIR` and recorded `fail` on eight sound tips (1498); PR 2362's `runner_env()` drops it. The before-merge form stays open, below the floor [false red][source20].
- Live Zotero tests skip "no display" in every gate; one failed under a green `make check`. Run them by hand with `DISPLAY=:0` before landing `scripts/zotero.py` changes [13f6][source22].
- Flakes, cause not established: pool/kill-group tests, two `idh` lifecycle tests at 60 s [1322][source11]; `test_guard_destructive_bash` pgrep once [ce1c][source23]; a `make check` stalled at 98% for 9 min once [f7aa][source24].
- The after-merge runner deletes inherited `IDH_SESSION_*` (PR 2097) [leak][source12]. A stuck required check: do not block on `--watch` [velocity][source14].
- Killed test runs leave `idh-tracked-*` in TMPDIR, below the floor. Skill-card size counts only once tracked [1541][source15]. `close-and-clean.sh:67` names the check from the last printed note, wrong after an untagged `bump` (open `consider:`, 1381) [source16]. run_pool waits on its own pids (PR 2105); an over-limit race on a 127 return remains [source10]. Snapshotting a target FIFO once hung the test-target probe [diagnostics].
## Open questions
- Is the forge ruleset still seven required checks, no bypass? Unverified. Gaze wall time is model turns (~67 s orchestrator, derived). On a project with no declared check set, verify-gate ran pytest twice (cadens PR 63) [monitoring][source17].

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../design/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../design/memory-v8/source-revisions.tsv).
- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md); [PR #1245](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md); [1082](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md)
- [Doctors landing](../journal/2026/2026-10-27-harness-doctor-and-project-coherence.md); [1240](../journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md); [rename](../journal/2026/2026-10-27-test-doctor-rename-1228.md); [wall time](../journal/2026/2026-10-27-trace-wall-time-pr1722.md); [yawn](../journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md); [practice](../journal/2026/2026-10-28-doctor-practice-and-catalog-links.md); [triage](../journal/2026/2026-10-29-harness-doctor-triage.md); [1088](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md)
- [1419 closure](../../tickets/closed/1419-after-merge-red-39718125e6a6.erg) (named cause caller-reported, not re-isolated); [2362/2370 landed](../journal/2026/2026-11-10-roar-pr2362-pr2370-false-red-ended.md).
[diagnostics]: ../journal/2026/2026-11-07-raid-train-controls.md

[source1]: ../journal/2026/2026-10-29-test-doctor-gate-contention.md
[source2]: ../journal/2026/2026-10-21-pulse-gate-wall-time.md
[source3]: ../journal/2026/2026-10-30-test-doctor-reruns-probe-1367.md
[source7]: ../journal/2026/2026-10-30-python-tool-baseline-github-runner.md
[source8]: ../journal/2026/2026-10-06-local-ci-act-equivalence.md
[source10]: ../journal/2026/2026-10-31-t1396-run-pool-throttle.md
[source11]: ../journal/2026/2026-10-28-after-merge-red-1322-cleared.md
[source12]: ../journal/2026/2026-10-31-t1396-session-identity-leak.md
[source14]: ../journal/2026/2026-10-21-velocity-scan-stale-baseline.md
[source15]: ../journal/2026/2026-10-21-pulse-testing-expert-1541.md
[source16]: ../journal/2026/2026-10-31-t1381-result-names-checks.md
[source17]: ../journal/2026/2026-10-31-monitoring-and-data-locations.md
[source18]: ../journal/2026/2026-11-10-test-doctor-check-fast-workers.md
[source19]: ../journal/2026/2026-11-09-raid-1488-single-ticket.md
[source20]: ../journal/2026/2026-11-09-weekly-ticket-audit-and-false-red.md
[source21]: ../journal/2026/2026-11-09-raid-1483-paper-skill.md
[source22]: ../journal/2026/2026-11-10-roar-raid-13f6d8-zotero-attach-licence-and-embedded-title.md
[source23]: ../journal/2026/2026-11-10-roar-raid-ce1c5a-raid-land-nested-worktree.md
[source24]: ../journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md

## Fallback
