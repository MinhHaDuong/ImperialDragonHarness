---
name: fork-skills-bare-context
description: "context:fork Skill invocations start bare — args arrive but doc-style SKILL.md reads as documentation; forks don't inherit cwd; drift falls back to ambient cues"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9c19a8ad-7f76-4f61-8a96-84d3d6d01758
---

A `Skill(context: fork)` invocation starts from a BARE context: the only user
message is the SKILL.md body with `$ARGUMENTS` interpolated. It does NOT
inherit the caller's conversation or cwd (it lands in the session worktree on
whatever branch is checked out there), and it DOES see the parent's
session-start gitStatus snapshot, worktree name, and shared task list.

**Why:** 2026-06-03/04 raids — 4 of ~14 forks (then 3 more) read the doc-style
body as "skill documentation loaded, no explicit task" and fell back to ambient
cues, producing wrong-branch reviews and rogue PR #243. Drift is stochastic on
byte-identical input, so prompt fixes only reduce frequency.

**How to apply:** When authoring a fork-context skill, open with a TASK
DIRECTIVE block (execute now / cd into the passed worktree= path / STOP on
missing args / never infer a task from the environment) — pattern + ratchet
tests shipped in IDH PR #262 (`tests/test_verify_fork_contracts.py`). For
safety (not just frequency), prefer `Agent(isolation:"worktree")` spawning with
an imperative prompt — raid execute agents never drifted. Escalation path lives
in IDH ticket [[0202]]; see also [[rogue-agent-pattern]].
