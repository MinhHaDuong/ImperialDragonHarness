# Raid 6530fd: runtime.py notify, launch and session verbs (1312-1314)

Date: 2026-10-28. Tickets 1312, 1313, 1314 (children of tracker 1309).
PRs #1899 (notify), #1897 (session), #1901 (launch), all merged at their
gate-ruled heads; merge commits e75aa0ca, 7099ed9a, 8a5877d4.

Events:
- Three sonnet coders ran wave 2 in parallel from WAVE_BASE c3492b2a. The
  shared registry (`VERBS` in scripts/runtime.py) was pre-coordinated by
  brief, not by a Phase 5.0 PR: each PR wrote a byte-identical
  `assert runtime_wake in runtime.VERBS` line in tests/test_runtime.py, which
  merged clean; the import and list lines conflicted as expected.
- PR #1897 first headed 2b49a0ab with a hunt-phase gaze REVIEWED that ran no
  model seat. Its `headless` read `CLAUDE_CODE_CHILD_SESSION`. From the raid
  lead, a live Claude Code subagent (CLAUDE_CODE_CHILD_SESSION=1,
  CLAUDE_CODE_ENTRYPOINT=cli) whose background wake fires,
  `runtime.py can wake` answered YES on main and NOOP on that head. The
  ticket annotation had asked for that marker. Fixed red-first in b7641297;
  the raid's gaze reproduced the regression on the parent and its absence on
  the fix.
- PR #1899's hunt-phase gaze recorded `seats: self-only`; the raid re-ran
  gaze with a cross-family seat (gpt-6-luna), REVIEWED.
- PR #1901 first trimmed author wording in rules/claude-code.md to fit a new
  bullet under RESIDENT_BUDGET. The raid lead moved the contract line to
  skills/route/routes-recommendations-claude-code.md § Launching and restored
  the rules file byte-for-byte (af137a66).
- A `--force-with-lease` push after a rebase was refused by the permission
  classifier (1313 coder; PR #1900 closed, superseded by #1901). Later
  sibling conflicts were resolved by merging origin/main into each branch
  (a846e89f, 74f8d86b) instead of the wave-rebase procedure; each merge
  commit got a narrow gaze before its gate.
- `merge-gate.py tier --since <ruled tip>` answers `full` after any conflict
  resolution ("the approved tip no longer merges cleanly"), so each sibling
  conflict cost one narrow gaze.
