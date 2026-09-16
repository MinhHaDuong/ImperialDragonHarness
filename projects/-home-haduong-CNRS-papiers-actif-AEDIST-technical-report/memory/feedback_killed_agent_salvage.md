---
name: killed-agent-salvage
description: "Killing a raid subagent mid-execution leaves orphan worktree + locked branch + uncommitted WIP. Don't force-remove without salvaging first."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc8db06a-aaf1-4fe0-a819-b5271e0d6403
---

When you `TaskStop` a raid subagent that is mid-edit, it leaves three things behind:
1. The worktree directory under `.claude/worktrees/agent-<id>/` (git-locked).
2. The branch it created (claimed exclusively to that worktree).
3. Uncommitted WIP in the worktree's working directory.

**Lock persists even after clean completion** (raid 0183/0187/0191, 2026-05-21):
agent worktrees stay locked after the subagent exits normally — the lock is
set at creation by the harness, not released on exit. Post-merge cleanup
always needs `git worktree unlock <path>` before `git worktree remove --force`
will succeed; `gh pr merge --delete-branch` also fails its local-branch
deletion step when the branch is still claimed by a locked worktree. The
GitHub-side squash succeeds regardless — verify via `gh pr view <N> --json state`.

**Salvage pattern** (cheap, no work lost):
1. `cd` into the orphan worktree → `git add -A && git commit -m "WIP: salvaged from interrupted raid"`.
2. `git push -u origin <branch>` so the WIP survives even if the worktree dies.
3. `git worktree unlock <path> && git worktree remove <path>` → branch persists, working dir gone.
4. Relaunch a finisher subagent with `git switch <branch>` (NOT `-c`) and instructions to complete remaining steps + a final commit + PR.

**Why:** Vécu pendant raid SOTA adapters 2026-05-20 — j'ai tué 4 agents mid-execution, leur worktrees ont gardé branch lock. Sans salvage, `git worktree remove --force` aurait perdu 4 × adapter file + tests + fixtures (~1500 lignes de WIP). Salvage = 4 commits "WIP" + 4 push, ~3 min total, puis finisseurs reprennent proprement.

**How to apply:** Avant tout `worktree remove --force`, vérifie `git status` dans la worktree. Si uncommitted, salvage en deux commits (WIP + finition) plutôt que de jeter. Liée à [[raid_budget_recovery]].
