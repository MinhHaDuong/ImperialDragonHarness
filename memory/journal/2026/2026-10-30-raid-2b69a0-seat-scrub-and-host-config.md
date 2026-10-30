# Raid 2b69a0: seat stderr scrub (1370) and seats sealed from host CLI config (1371)

Date: 2026-10-30. Host: padme. Tickets 1370 and 1371 closed.
PR #2048 merged as aefbb075, PR #2050 merged as 4e942889. Follow-ups 1375
(scrub residuals, unscrubbed seat body) and 1376 (seat inherits the caller's
`CLAUDE_*` environment) filed in PR #2051.

- Workers: plan agents claude-sonnet-5-5; blind-spot pass claude-opus-5-5;
  executors claude-sonnet-5-5 (1370) and claude-opus-5-5 (1371).
- The blind-spot pass said the claude door loads user settings under
  `--safe-mode` (`~/.claude/settings.json` sets `effortLevel` low). The 1371
  executor found the door already carries `--restricted`, which per
  `claude --help` ignores user, project and local settings files; the missing
  piece was an effort pin, so the door gained `--effort medium`, not the
  planned `--setting-sources project`.
- Codex check without a model call: without `--ignore-user-config` the seat
  resolved effort `low` and ran the host SessionStart hook; with it, effort
  `none` and no hook; the `-c` medium pin applied either way.
- Real launches on the new doors, each quoting a planted nonce: codex
  gpt-6-luna 22 s, claude haiku 14 s, pi padme local model 100 s.
- The 1370 hunt's gaze wrote answer 20261030T133018069Z-padme-31475f66 with
  `result: REVIEWED`, `seats: self-only` and `plan check: FAIL — manifest
  unreadable`: on this cross-family-consent host the plan held only a self
  item without a `--no-cross-family` reason, no manifest was written, and
  `gaze_close.py` recorded the answer anyway. The raid re-ran gaze with an
  openai/gpt-6.1-sol seat, which reproduced three leak shapes; the
  orchestrator fixed five shapes (7f9d846a) and a third gaze reviewed them.
- The 1370 executor adopted the raid's own session worktree
  (`t1370-1259116-10226`, created clean by the orchestrator under that name)
  as its ticket worktree. The raid moved to a new session worktree.
- When `raid_land.py --cleanup` removed that worktree, two processes started
  from it failed: a 1371 gaze run's `gaze_close.py` crashed in
  `containment()` (rerun from its own worktree recorded fine), and the
  sitrep wake exited 1 on `getcwd`.
- Attribution capture failure: PR #2048's block is refused by
  `attribution_record.py` (`--from-notes pr:2048`, `--capture-unit pr:2048`)
  with `line 11: duplicate finding within one reviewer attempt`; the PR body
  carries no attribution block. PR #2050 captured as
  `memory/evidence/attribution/2026-10-30-review-attribution-pr2050.md`.
- Both gates APPROVED in round 1 (sessions 2be0fd39…, e9b05364…).
