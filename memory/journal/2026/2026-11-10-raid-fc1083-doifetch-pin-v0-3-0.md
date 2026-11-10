# Raid fc1083: DOIfetch pin moved to v0.3.0 (ticket 1513, PR 2421)

Date: 2026-11-10. Project: ImperialDragonHarness. Launched by the author
typing `raid 1513` in an interface session (claude-fable-5-2).

## Context

Ticket 1513, filed the same morning from the DOIfetch session that cut the
release, asked to move the pin from v0.2.0 to v0.3.0 in `scripts/doifetch.sh`,
`pyproject.toml` (lock refreshed) and `STATE.md`.

## Events

- The lead read the premise back from the remote before any launch:
  `refs/tags/v0.3.0` is object d76db1f, peeled 95efea6.
- Imagine: the per-ticket pass was skipped. The blind-spot pass
  (claude-sonnet-5-5, one read-only agent) read the upstream diff between the
  two tags from a throwaway clone: every name `scripts/fulltext_cascade.py`
  imports is unchanged, dependencies and extras are unchanged, upstream
  `DEFAULT_ORDER` gains a `core` source that the harness's own `OPEN_SOURCES`
  list does not carry.
- Plan and feasibility: the lead wrote both itself, with no agent, citing
  `rules/workflow.md` § Delegation ("Don't delegate simple work"); the raid
  skill's Phases 3 and 4 name an agent per ticket.
- `raid-sitrep.py` answered `UNREADABLE queue: no QUEUE line in the log`
  (exit 2) on the first sitrep after `RAID_START`; it read once a
  `QUEUE n=1` line was appended. `raid_log.py append PR ... n=-` was refused
  ("PR n= must be a number"): the `executing` step was logged only once the
  request had a number.
- Execute: one coder (claude-sonnet-5-5) forked from the wave base, moved the
  four sites, refreshed the lock with `uv lock --upgrade-package doifetch`
  (three lines each way in `uv.lock`), and opened PR 2421. Its evidence:
  44 fast-tier and 43 integration-tier tests passed on the four wrapper test
  files, `scripts/doifetch.sh --version` printed `doifetch 0.3.0`, and one
  fetch by DOI through the wrapper returned a PDF from the `hal` source.
- The coder's `make check` ended 4 failed, 3617 passed, 132 skipped after
  18m30s: `test_launch_line.py::test_unit_falls_back_to_the_git_branch_then_a_dash`,
  `test_skill_case_notes.py::test_cwd_outside_a_repository_is_a_no_note`,
  `test_smelt_native_notes.py::test_non_git_path_is_left_as_given`,
  `test_review_trajectory.py::test_unreadable_repo_is_not_checked`. The lead
  reran the four in the request's worktree with `TMPDIR` in a fresh directory
  under `/tmp`: 4 passed. One of them, rerun with `TMPDIR` set to the
  worktree's `.tmp`, failed again.
- Review: the gaze answer on notes (review `rv-20261110-pr-2421-62f9`, run
  `gz-20261110T122106917Z-09e8`) reads `result: REVIEWED`, `seats: panel`,
  review plan "check and self read; wrapper-tests (script, none), diff-read
  (claude-sonnet-5-5, anthropic)", telemetry `agents=0`. Its `attribution`
  field is an empty list.
- Verify-gate, run by the lead's session: APPROVED at round 1 on tip 9aa5f5e8
  (the reviewed head plus the ticket close commit), duration 2m23s as the gate
  reported it.
- Landing: the lead's own `raid_land.py 2421 --ruled-head <tip> --ruled-claims
  1513 --cleanup` ran unrefused; merge commit 3399f6fd, read back MERGED.

## Outcome

- Main pins DOIfetch v0.3.0 at 95efea6 in the three files and the lock;
  ticket 1513 is closed.
- Attribution capture failed for PR 2421: `attribution_record.py
  --capture-unit pr:2421` answered `attribution: not derivable: reviewers`,
  exit 0, and wrote no record under `memory/evidence/attribution/`. The two
  writer lines (plan: anthropic/claude-fable-5-2, execute:
  anthropic/claude-sonnet-5-5) are on the review's notes.
- `scripts/fulltext_cascade.py:129` still says HAL forms its query from the
  file name; at v0.3.0 that is the fallback after a lookup by DOI
  (`src/doifetch/sources/hal.py` at the tag). Left as is.
