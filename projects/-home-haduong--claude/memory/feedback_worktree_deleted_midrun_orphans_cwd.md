# Worktree deleted mid-run orphans the session base cwd

A background job whose session base-cwd worktree is DELETED mid-run
permanently loses `EnterWorktree` and cwd-dependent `Skill` invocations for
the rest of the session. The parked-cwd guard
(`scripts/guard-enterworktree-parked-cwd.sh`) denies both from the now-orphaned
base cwd, and a worktree-identity guard blocks a bare `cd <wt> && git`
compound as a substitute. There is no way back into a normal skill-driven flow
from that session once the underlying worktree directory is gone.

Working recovery used in raid-217 (ticket 0217, PR #564, 2026-07-13): drop to
manual isolation — `git -C <repo> worktree add <path> -b <branch>` — and drive
every git operation with absolute paths and `git -C`, never a bare `cd`.
Delegate every skill invocation that still needs cwd-resolution (`hunt`,
`gaze`, `merge`, `roar`) to `Agent(isolation:"worktree")` subagents: each gets
its own freshly registered worktree, which the parked-cwd guard exempts,
letting the skill machinery run normally even though the orchestrating
session's own cwd is unrecoverable.

Related: `feedback_worktree_path_trap_needs_guard.md` (the guard's origin),
`feedback_shared_worktree_live_session_contention.md` (a sibling worktree
hazard). This one is specifically about a worktree *disappearing* out from
under a running session, not about path confusion between live worktrees.
