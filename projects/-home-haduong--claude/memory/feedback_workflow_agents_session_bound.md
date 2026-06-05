---
name: workflow-agents-session-bound
description: Workflow-tool agents run in the SESSION checkout by default and worktrees are cut from the SESSION repo — isolation is opt-in, cross-repo runs need a session in the target repo
metadata:
  type: feedback
---

Workflow-tool `agent()` calls run in the session's checkout unless
`isolation: 'worktree'` is passed explicitly, and that worktree is cut
from the SESSION's repository — never from a path named in config.

**Why:** Probe-verified 2026-06-05 (ticket 0221) before the fang-audit
validating run: both the proven May prototype and its faithful
extraction omitted isolation — 16 concurrent mutate→test→revert agents
would have corrupted one shared tree — and a git-erg audit could not
launch from an IDH session at all (agents land in a tree without
src/go). A prompt line telling the agent "you are in an isolated
worktree" does not make it true; some agents then hand-roll /tmp
scratch worktrees to make it true, leaving detached-HEAD residue.

**How to apply:** Any Workflow script whose agents mutate files gets
`isolation: 'worktree'` on those call sites (read-only judges stay
non-isolated — worktrees are expensive). Any skill auditing a TARGET
repo must be invoked from a session rooted in that repo — say so in
its SKILL.md as a hard requirement. Cheap pre-spend check for any new
fan-out: a one-agent probe returning pwd/toplevel/worktree-list
(~22k tokens) before the expensive run. After runs, `git worktree
prune` the target repo — dirty (seeded) agent worktrees and /tmp
scratch worktrees survive auto-cleanup. See also
[[feedback-fork-skills-bare-context]] for the sibling fork-isolation
modes.
