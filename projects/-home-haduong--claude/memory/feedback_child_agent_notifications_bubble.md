---
name: feedback_child_agent_notifications_bubble
description: A background subagent's OWN background children can complete-notify the top-level session; treat such notifications as the delegate's internal traffic — don't act on them, wait for the delegate's own completion
metadata:
  type: feedback
---

During raid 376/377 (2026-07-28), the wave-2 execute agent (launched via
Agent, background) spawned its own background reviewer for its pre-PR
self-gate. When that grandchild finished, its completion notification —
full findings payload included — arrived in the *top-level session*, not
(only) in the delegating agent. The delegate was still mid-run; its own
completion notification arrived later with the findings already handled.

**Why:** a task-notification fires whenever an agent stops with no live
background children of its own; the routing surfaces grandchild
completions at the session level. Acting on one from the interface
session duplicates the delegate's in-flight work — the findings belong
to *its* loop (here: step-9 self-gate findings the executor proceeded to
fix itself). Intervening or "helpfully" fixing would have collided with
the delegate inside its own worktree.

**How to apply:** on receiving a completion notification, check whether
the task-id matches an agent *you* launched. If not, it is a delegate's
internal traffic: note anything strategically useful (scope extensions,
blocking findings), take no action, and wait for the delegate's own
task-id to complete. Judge the delegate on its final report — which may
already incorporate the grandchild's findings. Related:
[[feedback_supervisor_checkpoint_pattern]],
[[feedback_workflow_agents_session_bound]].
