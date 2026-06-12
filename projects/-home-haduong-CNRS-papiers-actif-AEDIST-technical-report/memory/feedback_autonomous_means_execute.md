---
name: Autonomous-while-away means execute, not plan
description: When user signals they're leaving and wants work done autonomously, kick off the autonomous skill directly — never sit in plan mode awaiting approval.
type: feedback
originSessionId: cdaa7a19-9651-4adf-ae9d-cf8d5e977b3b
---
When the user says "while I go to lunch" / "while I'm away" / "in autonomous mode" — they expect work to be running by the time they walk away. Do not write a plan file and call `ExitPlanMode` and stop. `ExitPlanMode` only requests plan approval; it doesn't execute. If plan mode is active and the user has signaled autonomous-while-away, exit plan mode early or just invoke the actual skill (`/raid`, `/schedule`, `/loop`) and start the work.

**Why:** 2026-04-30 — user asked if a raid + de-risk was feasible during lunch. I treated it as a planning exercise: assessed feasibility, wrote a plan to `~/.claude/plans/`, called `ExitPlanMode`. User rejected the tool, walked away, came back to nothing done: "Thanks for nothing."

**How to apply:**
- "While I'm away / at lunch / overnight" + a concrete task → invoke the autonomous skill in the same turn. Confirm scope with `AskUserQuestion` if needed, but the *next* action after confirmation is launching the work, not writing a plan-for-approval document.
- If currently in plan mode and the request is autonomous-execution-shaped: surface the conflict ("plan mode is on, this needs me to actually run things") and ask the user to flip the mode, instead of pretending the plan file is the deliverable.
- If session-start reminders include `EnterWorktree`, load and call it before substantive work — autonomous raids need worktree isolation.
