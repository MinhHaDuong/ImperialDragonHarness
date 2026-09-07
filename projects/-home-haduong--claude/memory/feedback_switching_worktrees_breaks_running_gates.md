---
name: feedback_switching_worktrees_breaks_running_gates
description: "The isolation guard tracks the SESSION's worktree, so an EnterWorktree or git switch while a /gaze fork is running strands that fork's Bash entirely — park the session until the gate returns"
metadata:
  type: feedback
---

A `/gaze` fork and its agents resolve their Bash against the *session's*
tracked worktree, not their own. Move the session — `EnterWorktree` to another
path, or `git switch` the tree the fork is standing in — and every Bash call on
that fork's line starts failing, including bare `pwd` and `echo`:

```
This session is isolated in the worktree <A>, but this command's working
directory resolved to the shared checkout (<B>). Refusing to run it there...
```

**Why:** on 2026-09-07 a gate on one PR lost all Bash mid-run because the
coordinator switched worktrees twice to merge two other PRs. The fork was
read-only-capable (the `Read` tool kept working) but could not run `git diff`,
`make check`, the suite, or spawn agents — so it stalled at a partial review.
A second gate later switched the coordinator's own worktree onto its subject
branch, which is the same mechanism seen from the other side.

The stranded agent's diagnosis was exact and its self-report was the giveaway:
it had never referenced worktree A and could not explain how A entered the
picture. **A guard message naming a path the agent never chose is evidence
about the session, not about the agent.** It correctly reported the observation
and held the cause; the cause was upstream and it had no way to reach it.

**How to apply:**
- While a gate is in flight, park the session. Do the merges after it returns,
  or run them from a worktree no gate is using.
- Sequence the wrap-up: gate → verdict → merge → move. Never merge PR N while
  PR M's gate is still running if the merge requires a worktree switch.
- When an agent reports Bash refusals naming a foreign worktree, do not ask it
  to work around them and do not read it as the agent's error. Tell it to stand
  down, then re-run the work yourself from a stable position.
- A fresh probe subagent hitting the identical error is confirmation the fault
  is session-level, not that agent's state.

Related: [[feedback_shared_worktree_live_session_contention]],
[[feedback_worktree_deleted_midrun_orphans_cwd]].
