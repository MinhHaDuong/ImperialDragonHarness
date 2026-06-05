---
name: feedback_verify_agents_dirty_main_repo
description: Verify sub-agents contaminate the invoking checkout — contracts shipped in IDH PR #262; 0202 validation done (headline clean, milder in-fork drift 3x) — spot-check stays until 0216 lands the Agent-spawn conversion
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 00214805-becd-45d2-b825-607057f60719
---

Verify sub-agents (`/verify`, `/verify-adherence`, `/verify-gate`) used to land
in whatever directory they were invoked from and contaminate it: 2026-06-03/04
raids logged eight incidents (resurrected `0149-*.erg` swept into a merge by
blanket `git add tickets/`; rogue PR #243 pushed from the orchestrator's local
branch; wrong-branch/off-task adherence and gate runs). Root cause pinned in
ticket 0193 (closed via PR #262, 2026-06-04): `context: fork` starts bare —
args arrive but doc-style SKILL.md reads as documentation, and forks don't
inherit cwd. See [[fork-skills-bare-context]] for the authoring pattern.

**Why:** the contracts shipped in PR #262 (worktree= threading, TASK DIRECTIVE
openers, verify Containment postcondition, erg-pr-merge staging narrowed to
erg-touched paths) are mostly frequency reducers — only the staging narrowing
is mechanical. The rogue-push mode is not yet deterministically killed.

**How to apply:** 0202's validation cycle completed 2026-06-04 (closed
2026-06-05): headline containment HELD — zero off-task runs, foreign files,
rogue pushes — but milder in-fork drift recurred 3x (under-execution,
out-of-role rebase attempt, malformed log line), so the escalation fired as
ticket 0216 (Agent-spawned sub-skills with pinned cwd). Keep the manual
spot-check after verify runs and before any `erg-pr-merge` until 0216 lands:
(1) `git status --porcelain` in the invoking checkout — discard foreign files;
(2) `gh pr list --state open` — close rogue PRs; (3) confirm the expected
branch. Known benign tail (2026-06-05): a gaze fork may leave the session
worktree detached or on the PR branch — re-switch, don't panic.

See also: [[feedback_rogue_agent_pattern]], [[feedback_parallel_execute_branch_contamination]]
