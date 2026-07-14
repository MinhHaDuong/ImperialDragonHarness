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

Re-confirmed 2026-07-14 (session a645ef77): the removed worktree's path can
persist as an empty husk directory that resolves into the PRIMARY repo, not a
worktree, once deregistered. The parked-cwd guard then denies `EnterWorktree`
(by design) and the worktree-identity guard blocks every non-`git -C`
mutation from that path. Recovery is unchanged — `git -C <primary> worktree
add` for manual isolation, plus delegating committable work and skill
invocations to `Agent(isolation:"worktree")` subagents. Husk detection in
`worktree-gc` shipped report-only (never removes) under tickets/0325.

Ticket 0338 investigated removal-by-heuristic and confirmed report-only as
the PERMANENT decision, not a first cut: a local liveness probe exists —
`[ -L /proc/<pid>/cwd ]` distinguishes a dead PID (not a link) from a live
same-host PID even without target-read permission (lstat needs none) — but it
is structurally blind to remote/network-FS sessions, which have no local
process to probe at all; that gap alone blocks a safe heuristic. A live near-miss surfaced during that
investigation — the raid session's own base cwd was itself an unregistered
husk with five live PIDs holding it as cwd, mtimes hours stale — reinforcing
that an age/mtime heuristic would plausibly have removed a live session's
cwd mid-task.
