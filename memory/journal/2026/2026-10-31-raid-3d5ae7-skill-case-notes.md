# Skill case notes stage 1 merged; typed slash commands bypass the Skill hook (ticket 1394, PR #2114)

Raid 3d5ae7, 2026-10-31. Merged as 68e7f6b8. Ticket 1394 stays open.

- Delivered: `scripts/skill-case-notes.sh`, wired in `adapters/claude-code/hooks/hooks.json` on
  `PostToolUse` (matcher `Skill`) and `UserPromptSubmit`; `memory/skills/merge.md` (four cases);
  `tests/test_skill_case_notes.py` (19 tests).
- Headless read-back, claude 2.1.316, haiku, planted token in a temp repo: main session and subagent
  quoted the token; a second load logged `already-delivered`. A typed `/merge` prompt produced no
  `PostToolUse` call on `Skill` in two runs (model answered NONE, no log line). An Imagine-phase probe
  had seen a typed `/probe` fire the hook once; the two observations were not reconciled.
  With the `UserPromptSubmit` trigger added, the typed read-back quoted the token with one `delivered` line.
- Interactive TUI not tested. The marker outlives compaction and `--resume`.
- Gate: round 1 REROLL (pipefail-guard: `set -uo pipefail`). The fix was rebased onto origin/main
  before round 2; round 2 was refused at admission because `review_notes.py gate_state` requires the
  rerolled head to be an ancestor of the new head. A delta re-gaze on the rebased head made it
  admissible; round 2 APPROVED. Ticket 1403 filed.
- The executor, launched with hunt `1394 inline`, worked in the orchestrator's session worktree and
  switched its branch to the ticket branch; the orchestrator switched it back and gave the PR its own worktree.
- A `bypassPermissions` headless launch in the read-back was refused by the classifier; reruns used
  `--allowedTools Skill`.
- Reviews were same-family only (Sonnet seats, Opus orchestrator).
- 1349: its rebuild run, PR #2049, merges cleanly with main (merge-tree, 2026-10-31) and has no gaze
  record; merging it is the author's acceptance (exit criterion 2). Not touched by this raid.
