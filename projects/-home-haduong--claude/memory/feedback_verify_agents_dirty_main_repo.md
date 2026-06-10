---
name: feedback_verify_agents_dirty_main_repo
description: Verify sub-agents contaminate the invoking checkout — contracts shipped in IDH PR #262; 0202 validation done (headline clean, milder in-fork drift 3x); structural fix landed (0216 Agent-spawn pinned-cwd + 0228 cwd-anchoring closed) — spot-check is now a fallback, not standing
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
ticket 0216 (Agent-spawned sub-skills with pinned cwd). 0216 and 0228
(cwd-anchoring across the fork boundary) have since closed (verified
2026-06-08) — the structural fix is in place, so the manual spot-check is now
a **fallback**, not a standing requirement. If you still observe drift after a
verify/fork run, the same three checks apply: (1) `git status --porcelain` in
the invoking checkout — discard foreign files; (2) `gh pr list --state open` —
close rogue PRs; (3) confirm the expected branch. Known benign tail
(2026-06-05): a gaze fork may leave the session worktree detached or on the PR
branch — re-switch, don't panic.

**Merging while the primary holds the PR branch** (recipe validated on PR #359,
2026-06-10): when the primary checkout sits on the PR branch (dirty, possibly
owned by another live session), don't move its files. From a fresh worktree:
(1) `git -C ~/.claude switch --detach` — frees the branch name in place, same
commit, dirty files untouched; (2) `git switch --ignore-other-worktrees <branch>`
in the worktree if the detach must be avoided (only safe when no commits will be
added, e.g. `Ticket: none`); (3) after the mandatory pre-merge rebase, the old
SHA the primary still sits on is no longer an ancestor of origin/main — verify
merge equivalence with `git cherry origin/main <old-sha> <base>` (`-` prefix =
patch already upstream), not `merge-base --is-ancestor`. The /roar pre-check
hits the same false negative after any rebase-then-merge.

See also: [[feedback_rogue_agent_pattern]], [[feedback_parallel_execute_branch_contamination]]
