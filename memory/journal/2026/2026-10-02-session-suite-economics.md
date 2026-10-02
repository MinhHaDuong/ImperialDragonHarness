# Session: test-suite economics — hermeticity guard landing, tiering, parallelism

## Context

The author challenged ticket 0940's premise (BASH_ENV hermeticity guard for
Python suites) as second-order guarding after 0945 removed ambient credential
residency. The session then ran the full hunt flow on PR #1111, three review
rounds, an author re-scope ruling, and a follow-on chain of suite-economics
work the author ordered interactively (check-fast tiering, xdist audit and
adoption, monolith profiling, one knob).

## Observable events

- Round 2 of PR #1111 found base drift (origin/main had added two suites with
  non-hermetic spawns) and three undisclosed false-negative classes in the
  guard; round 3 found one real in-tree leak (test_on_start_memory_injection
  hook_stdout passing os.environ.copy() to a bash child, runtime-proven with a
  sentinel) plus an unbounded adversarial evasion frontier (merge-order,
  comparand, walrus/getattr/importlib spellings) absent from the tree.
- The author ruled 2026-10-02: re-scope 0940 to the post-0945 threat model
  (machine-independence, project .env reach, residency ratchet); the
  adversarial tail is accepted-and-disclosed, not chased. PR #1111 merged with
  the re-scoped ticket body; 74 spawn sites across 32 files fixed via
  child_env(); guard is adherence-tier, 33 controls, 3 sentinel probes.
- Suite timing measured at each step: make check 81s; check-fast 18.4s with
  73% of it in 26 unmarked spawn tests in test_worktree_tools.py (1010,
  PR #1118 — re-tiered, check-fast 2.9s); lint 2.1s pinned at the pytest
  boot+collection floor (~2s to import 1265 modules); the author declined a
  ratchet subdirectory split (import migration + flat-glob coverage holes in
  the hermeticity guards outweigh ~1s on lint).
- xdist worker-safety audit (1011, PR #1120): static census clean on
  environment/filesystem/git-state axes; three parallel trials reproduced the
  serial counts exactly. Author chose option 1: pytest-xdist pinned, -n 4
  wired into check-tests and CI. test_makefile_gates' bare-recipe regex was
  stricter than its cited rule ("everything"); amended to permit exactly
  -n N, nothing else. Full check 81s -> 37.6s.
- Monolith xtrace profile (per-command PS4=$EPOCHREALTIME timestamps):
  erg_pr_merge uniform fixture cost (median 0.27s x 47 cases); seat_runner
  bimodal with 5.09s in the relay-socket readiness loop burning its full
  50x0.1s bound in a test that stubs python3 (1012, PR #1122 —
  SEAT_RELAY_WAIT_TICKS knob, suite 9.6s -> 5.0s, full check 33.1s).

## Outcome

Four merged PRs (#1111, #1118, #1120, #1122), tickets 0940/1010/1011/1012
closed and archived. Full check 81s -> 33s; check-fast 18.4s -> 2.9s; CI
pytest-guard expected ~1m26s -> ~50s. The parallel floor is erg_pr_merge's
12.2s; the per-case sharding refactor is recorded in 1011 as below-threshold.

## Decisions already made

- 0940 re-scope ruling recorded in the ticket log and body (author, 2026-10-02).
- xdist adoption decision 1 recorded in 1011's log (author, 2026-10-02).
- Ratchet subdirectory split declined by the author ("2s is fast enough").
- The two sibling poll loops (seat-runner.sh:420 in-container,
  padme-reviewers.sh:42) swept and left: neither costs test time today.

## References

- tickets/closed/0940-hermeticity-guard-does-not-cover-python.erg
- tickets/closed/1010-spawn-based-suites-sit-in-check-fast-re.erg
- tickets/closed/1011-worker-safety-audit-pytest-xdist-paralle.erg
- tickets/closed/1012-seat-runner-relay-readiness-loop-burns-i.erg
- tests/test_python_tests_are_hermetic.py, tests/child_env.py
