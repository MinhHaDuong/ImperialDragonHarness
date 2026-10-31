# PR 2105: run_pool throttle limited to the pool's own pids (2026-10-31)

Context: after PR 2102 the after-merge record on ae970e19 was red on
`test_local_ci_parallel.py::test_pool_does_not_wait_for_the_callers_other_background_jobs`,
also red on 798d584b, green on other tips. Ticket 1396.

Events:
- Hypothesis: the bare throttle `wait -n` in `ci-local/common.sh` `run_pool` can
  block on the caller's background job. Not reproduced: 0 of 400 idle runs, 0 of
  3600 under 24 parallel loops. Cause not established.
- Author chose to apply the throttle fix anyway (`wait -n "${pids[@]}"`), right on
  reading. Gaze (script seat) reproduced a different defect on main that the fix
  removes: a caller job ending during the pool counted as a pool slot, 3 jobs ran
  against a limit of 2. A pre-existing over-limit race on a 127 return remains.
- verify-gate APPROVED round 1; merged at b752aec9.
- Attribution capture for PR 2105 wrote no record: `attribution_record.py
  --capture-unit pr:2105` reported `not derivable: reviewers`; the only gaze item
  was a script seat, and gaze_close did not take finding lines for it.
