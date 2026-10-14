# Roar exit tail scripted (1098) after the 1090 remeasure — 2026-10-14

Project: ImperialDragonHarness. Public audience: tickets, PRs and PR
comments only.

## Context

- The 1090 remeasure ([entry](2026-10-14-roar-remeasure-1090.md), PR #1403)
  found 1084 saved no roar turns against a same-method October control
  (median 10 → 12.5). The exit tail from preflight to the end took 7-21 tool
  calls (median 10, n=4).
- Two roars after PR #1398 (padme sessions `3f82806b`, `d331a70c`) ran the
  new sync of local `main` before `ExitWorktree remove` and were still
  refused ("Worktree has N commits"). Ticket 1097 was reopened with that
  evidence (PR #1405).

## Events

- PR #1406: one sentence in roar step 7 making the script's exit code the
  verdict. A same-family reviewer returned 4 findings (the first wording
  collided with step 9a's fresh preflight); all adopted before merge.
- Ticket 1098 / PR #1409: `close-and-clean.sh --phase exit-check` and
  `after-exit --remove-worktree`. Author instruction: "only reasonable
  safety checks".
- /gaze round 1 (anchor 9291fabe): ESCALATE. The cross-family seat
  (padme/qwen3.8-27b, after huggingface/deepseek-ai/DeepSeek-V4-Flash failed)
  found that `git worktree remove` deletes ignored files and that the new
  SKILL text claimed otherwise. Author decisions: wording fix only, the scan
  stays with ticket 1095; the main-checkout-branch and main read-back checks
  stay non-gating notes.
- While #1409 was in review, PR #1407 (ticket 1077) retired `EnterWorktree`
  and `ExitWorktree` and rewrote the same roar step 9. The rebase conflicted
  in SKILL.md, close-and-clean.sh and tests/test_branch_cleanup_recipes.py;
  the resolution replaced `ExitWorktree keep` with `cd` to the main checkout.
- /gaze round 2 (anchor f9d54f61): REROLL on stale PR text and a label, fix
  commit 9ba9dfb9, then APPROVED. All three cross-family attempts failed
  (padme/qwen3.8-27b empty output twice after a positive control,
  padme-35b/qwen3.6-35b-a3b connection error); no independence claimed.
- Merge: the first `erg-pr-merge` run closed ticket 1098, pushed the close
  commit e6c91688 and exited 1 without arming auto-merge. The reason was in
  output truncated behind about 500 lines of `erg check` WARN lines; cause
  not established. A re-run accepted the closed ticket as a no-op and armed
  auto-merge; #1409 merged.
- PR #1403's body used `Closes 1090`, which the close-claim grammar does not
  parse; the forked session closed 1090 in PR #1408.
- In this session the `EnterWorktree` guard refused many compound shell
  commands and blocked the gaze seats from the `review-1409` tree; seats read
  the session worktree at the anchor instead.

## Outcome

Roar step 9 is now: exit-check → `cd` to the main checkout → the printed
`after-exit` command (about 3 actions, estimate, not measured). Turn savings
are to be measured with `roardeep.py` (1090 evidence folder) against the
October control once about 10 roars have run.
