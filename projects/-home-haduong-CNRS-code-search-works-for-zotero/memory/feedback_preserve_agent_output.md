---
name: feedback-preserve-agent-output
description: An agent's uncommitted output dies with its worktree — preserve the artifact itself, not just the report describing it
metadata:
  type: feedback
---

Before removing an agent's worktree or deleting its branch, check for
**uncommitted work in the tree**, not only for the report file the agent said
it produced. A subagent told not to commit leaves its entire output uncommitted
by construction, so `git worktree remove` destroys it with no reflog and no
recovery.

**Why:** on 2026-08-29 a voice-rewrite pilot produced two artifacts — a report
(`VOICE-PILOT.md`) and the rewritten `CONSTRAINTS.md` it described. The cleanup
sweep copied the report into the repo, confirmed it safe, then removed the
worktree and deleted the branch. The rewrite itself was uncommitted and is
gone; only the before/after excerpts inside the report survive. The check that
was run — "is the report preserved?" — returned yes while the more valuable
artifact was being deleted.

The general shape: an artifact *about* the work is not the work. A cleanup
check that inspects the description rather than the tree cannot see what it is
about to destroy.

**How to apply:** run `git status --short` in the worktree before removing it,
and treat any modified or untracked file as output to preserve or explicitly
discard. Better, when the output is worth keeping, tell the agent to commit to
its own branch and push it — then cleanup cannot lose anything, and the
worktree stays throwaway as intended. Reserve "do not commit" for agents whose
output is genuinely a report the caller will relay.

Related: [[feedback-decision-briefs]].
