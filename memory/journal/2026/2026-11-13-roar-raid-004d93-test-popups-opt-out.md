# Raid 004d93: PR 2486 and ticket 1550, test runs raised real main-is-red popups

Date: 2026-11-13 · host: padme · drafter anthropic/claude-fable-5-2

## Context

A climate-finance-het session filed ticket 1550 through PR 2486: harness tests
that drive a red after-merge run in a fixture repository put real "main is
red" popups on the author's desktop (the alert of ticket 1543, PR 2472). The
author handed the PR to a harness session ("PR2486 for you"), then asked for
`raid 1550`.

## Events

- **Landing PR 2486.** Bookkeeping tier (one ticket and its claim). No
  worktree held the branch; the session made one and ran `raid_land.py` with
  `--ruled-head - --ruled-claims -`. Read-back `MERGED 64d6727ea`, merge
  33 s, after-merge pass on 8b015ad8b.
- **Imagine.** The lead did the per-ticket reimagine inline and named two fix
  shapes: an environment opt-out read by `runtime_notify.popup()`, or a stub
  `notify-send` ahead on PATH. The Blind-Spot pass (Opus, read-only, 80 s)
  returned two findings, both checked by the lead: the hook starts the runner
  with its cwd inside the git directory, where `git rev-parse --show-toplevel`
  exits 128 and `--git-common-dir` answers, and the script may belong to
  another repository; and `runner_env()` passes the starter's environment to
  the detached runner, so an opt-out exported wider than pytest would silence
  real alerts. Both went into the executor's brief. Plan and feasibility
  phases were not run as separate agents; no annotation commit was made.
- **Execute.** One coder (Sonnet 5.5) ran hunt in its own worktree for about
  20 minutes and opened PR 2489: `IDH_NO_POPUP`, set by an autouse fixture in
  `tests/conftest.py` only; a result line naming the suppression;
  `repo_label()` from the common git directory; a positive-control test that
  moves a fixture's main through the real hook with the script outside the
  fixture. While it worked, its `dbus-monitor` recorded about 22 popups with
  the old title; other sessions' pytest and `merge-gate.py run` processes on
  the old tree were running at the time; which session sent them was not
  isolated. Its first unprotected `make check` timed out at 590 s with two
  failures, with TMPDIR inside the worktree; the two failures were not
  isolated.
- **Verify.** The coder's gaze was REVIEWED with `seats: self-only` and a
  logged deviation, the diff touching `scripts/merge-gate.py`. The lead ran a
  second, narrow gaze with one OpenAI red-team seat (gpt-6.1-sol, headless
  Codex): REVIEWED, panel, three considers, none fixed: runner scratch under
  the ambient TMPDIR, the detached runner not waited for, the forge login
  reaching the fixture runner. The lead checked the third: `GH_REPO` and
  `GH_HOST` unset, and `tests/test_after_merge.py:711` on main already starts
  the real runner with `--open-ticket` through the same environment.
  Verify-gate round 1: APPROVED on 494da7b49. Its probe bound a recording
  stub over `/usr/bin/notify-send`: 22 calls on the base over four red-run
  test files, 0 on the head over the same files and over the full suite
  (3745 passed, 150 skipped).
- **Landing PR 2489.** `raid_land.py` ran without a permission refusal.
  Read-back `MERGED 494da7b49`; after-merge pass on 7c299b167
  (pytest-guard 85.4 s).
- **Defect backfill.** Not run: the record of PR 2472 holds gaze answers at
  four reviewed heads (0050dbd76, 5f30dfd8d, 20564d705, 9af4df7e7).

## Outcome

Ticket 1550 closed by PR 2489. Timing from the lead's gaze to merged:
gaze 6m49s, gate round 1 8m17s, merge 38s, total 17m47s.

## References

- PR 2486, PR 2489, PR 2472; tickets 1550, 1543.
- Review `rv-20261113-pr-2489-aee9`; gaze answers
  `20261113T132224483Z-padme-98d84ef5` and
  `20261113T133019288Z-padme-2920f5cf`; verdict
  `20261113T134015899Z-padme-d77f4064`.
