---
name: feedback-bash-cd-primary-repo-trap
description: "In a worktree session, prefixing Bash with `cd /home/haduong/<repo>` routes git mutations to the PRIMARY repo on main, not the worktree"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: eddfaf5e-039e-4186-8b55-bc86650e69c0
---

In an EnterWorktree session the Bash shell already sits in the worktree
(`.claude/worktrees/<name>`) and resets there after every command. Prefixing a
Bash command with `cd /home/haduong/aedist-technical-report &&` cd's into the
**primary repo** (checked out on `main`), so any `git`/`erg close`/`git commit`
in that command mutates the primary repo on main — not the worktree branch.

**What it caused (2026-06-03):** picked t0353, branched correctly in the
worktree, then ran `cd /home/haduong/aedist-technical-report && erg close … &&
git add -A && git commit`. The close + a 493-file `git add -A` (pre-existing
untracked experiment outputs) landed as a commit on the **primary repo's main**,
not on t0353. Caught only because the commit message said "1 file" but status
showed hundreds. Recovery: `git reset --mixed HEAD~1` on primary, `git restore
--staged .`, `git checkout -- <ticket>`; then redo the close in the worktree.

**Why:** sibling lesson to [[feedback_main_repo_on_foreign_branch]] and the
Edit/Write worktree-path rule — same root cause (operations leaking to the main
checkout), different tool surface (Bash `cd`, not Edit/Write paths).

**How to apply:**
- Do NOT `cd /home/haduong/<repo>` in Bash during a worktree session. The shell
  is already in the worktree; run git/erg bare so they act on the worktree branch.
- If a tool (erg) needs the repo root, it's already there — `./tickets/erg …`
  resolves inside the worktree.
- Never `git add -A` when untracked data files are present (the repo carries
  hundreds of untracked `experiments/derived|outputs/*.record.json`). Stage the
  exact file: `git add tickets/NNNN-*.erg`.
- After any commit, glance at `git show --stat HEAD | tail -1` to confirm the
  file count before pushing.
