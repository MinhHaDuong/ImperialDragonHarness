---
name: haiku-truncated-final-reports
description: "subagents (haiku ×2, fable ×1) ended turn on a narration line instead of finishing — do mechanical checks inline, demand one-line verdicts, prompt executors 'do not end turn until the PR is OPEN', recover with a finisher agent on the same worktree"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80e1db00-3efc-4f2b-9331-9c8d6143972a
---

During raid 557 (2026-06-12), two consecutive `model: haiku` feasibility
agents ended their turn on a process-narration line ("Now let me compile
the final verification report:") and never emitted the actual numbered
PASS/FAIL list — even after the relaunch prompt explicitly said "your
final message must be ONLY the verdict list".

**Why:** haiku ends its turn after narrating intent instead of producing
the long structured final message; the Agent tool returns whatever the
last text was. Two relaunches cost more than the checks themselves.

**How to apply:** for haiku-tier mechanical verification, either (a) run
the handful of greps inline in the orchestrator (they're cheap — that's
what worked), or (b) keep the haiku agent's required output very short
(a one-line verdict, not a multi-section report). Reserve long
structured final reports for sonnet and above. Related: [[gaze-fork-dies-in-background-jobs]].

**Not haiku-specific (2026-06-12, raid 0567):** a `model: fable` EXECUTE
agent ended its turn mid-task on "waiting on the make check verdict before
pushing" — work done, never pushed, no PR. Mitigations that worked: (1)
executor prompts state "do NOT end your turn until the PR is OPEN —
implement → make check → push → gh pr create" (the three subsequent waves
all completed); (2) recovery = a finisher agent pointed at the SAME
worktree/branch (inspect `git status` + `git log` first, then finish) —
never restart from scratch, the work is sitting there committed or staged.
