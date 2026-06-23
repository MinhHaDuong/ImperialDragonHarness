---
name: feedback_enterworktree_stuck_cwd
description: EnterWorktree resolves the wrong repo when the session base cwd is parked outside the project; fall back to manual git worktree add
metadata:
  type: feedback
---

`EnterWorktree` (and cwd-dependent skills like `/verify-adherence`, `/review-pr`) resolve the git repo from the **session base cwd**, not from where your last `cd` landed. If that base cwd gets parked *outside* the project repo, they target the wrong repo silently.

**How it happens:** a `cd ~/.claude/projects` (e.g. for a Claude-cache op) becomes the session base; a later `ExitWorktree` restores the session to that same base. From then on `EnterWorktree t160` creates the worktree under `~/.claude/.claude/worktrees/t160` (the harness repo) instead of the project — because `~/.claude` is the nearest git repo to the parked cwd. An in-command `cd <project>` does NOT fix it: the base resets after every Bash call.

**Why:** worktree-rooted tools key off the harness's notion of session cwd, which only changes via EnterWorktree/ExitWorktree, not a plain `cd` (2026-06-19, ticket 0160 hunt).

**How to apply:** when the base cwd is stuck off-project, do NOT rely on `EnterWorktree` or cwd-dependent skills. Instead:
- Create the worktree manually: `git -C <repo> worktree add <repo>/.claude/worktrees/<name> -b <branch> origin/main`.
- Mimic `.worktreeinclude` by hand: `cp <repo>/.env <wt>/.env` and `<repo>/.dvc/config.local`.
- Drive everything with absolute paths and `git -C <wt>`; verify ownership with `basename "$(git -C <wt> rev-parse --show-toplevel)"` == the worktree name.
- For the merge gate, run the mechanical checks directly (`make check-fast` = ruff + tests) instead of the skill, and self-review; note this in the PR so `/gaze` can still run.

See [[project_reorg_0159_relocation]] — this surfaced during that reorg's follow-up.
