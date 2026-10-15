# Fourth Hoard merge and postmerge fixture failure — 2026-10-15

Project: ImperialDragonHarness. Audience: public repository/forge outcomes and
non-secret validation facts. Runtime: Codex; served provider-qualified model
pin and effective effort unavailable. This is factual capture, not a rule or
consolidation pass.

[PR #1438](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1438)
merged as `82ad5096d31d2c70959d0fa75d7d588b62907167` at 19:57:19Z after the
author requested merge, roar and lair. All ten forge PR checks passed. Local
CI on padme at head `cec0f664fd22b960c82e8372c5946f5b00ec72f4` passed all ten
jobs, including 1633 pytest passes and 10 skips. Exact integrated-main
`make check` passed 1640 tests, 3 skipped in 51.97 s. The PR had no recorded
review; no review-attribution record was manufactured.

Roar's close-claim audit examined 30 recent PRs, parsed 14 claims across 11 PRs
and found zero dropped/unresolved claims; four bodies had no recognized Ticket
line. Its exit and explicit-branch cleanup passed and removed only this task's
worktree and branch. No new defect-attribution backfill was commissioned by
the editorial consolidation. Housekeeping retained the foreign Arena checkout
and opaque-locked CI worktree. The scratch sweep removed three orphan
folders (12 KB) while retaining two live sessions. Yawn's fast probe passed
987 tests; none of the seven open tickets had exclusively mechanical
string/file/symbol exit criteria, so none was auto-closed.

The [postmerge main CI run](https://github.com/MinhHaDuong/ImperialDragonHarness/actions/runs/38798044900)
failed one test: `test_hoard_real_migration_from_another_project_cwd` in
`tests/test_skill_seam.py:250`. The assertion compared the unrelated project's
entire file-byte snapshot, including `.git/`. The reported only difference
was removal of `.git/objects/maintenance.lock` (empty bytes); no project source
or journal difference appeared. The run recorded 1 failed, 1632 passed,
10 skipped. This failure did not appear in the PR, local container or main-host
runs above.

The housekeeping fixture change adds per-invocation `maintenance.auto=false`
and `gc.auto=0` to its Git helper, retaining the complete byte comparison.
All ten tests in `test_skill_seam.py` passed in 2.76 s after the change.
The main failure's complete log was read locally; only the bounded facts above
are captured. No repository-wide Git setting was changed. The fourth report's
index label is refreshed to accepted after its merge; historical report and
journal bytes remain unchanged. STATE receives the current handoff and known
open ticket/PR facts on this same housekeeping branch.

Housekeeping validation after the fixture change: full `make check` passed
1640 tests, 3 skipped in 50.99 s, including catalog, agnostic and personal-data
checks. The test still compares all bytes of the unrelated project; no lock
path was excluded from its comparison. There was no rule or harness-setting
change and no new policy or ticket was proposed.
