# Worktree ownership, lock reason, and gc reclaim

The step-4 contract for a hunt worktree: how to write the lock reason so the
owner is checkable, and the conditions under which `worktree-gc` later reclaims
the tree. No normal hunt run traverses this; it is here for anyone debugging a
stranded worktree or a lock that will not clear.

## The owner pid in the lock reason

`<owner-pid>` is the long-lived runtime process: `echo $PPID` in the Bash tool,
whose shell is the runtime's child. **Not** the `bash -c 'echo $$'` child, which
dies at once and would let `worktree-gc` unlock a live tree.

If `$PPID` prints 1, the shell runs in a pid namespace (a sandboxed runtime)
and the owner is not visible: write the reason without a pid —
`hunt t<id> (owner pid not visible)`, never `(pid 1)`, which on the host names
init.

## When worktree-gc reclaims an ownerless tree

`/roar` removes the tree when its integration is ready. If the session dies
first, `worktree-gc` reclaims the tree once its branch is gone upstream (merged
and pruned) and two more things hold:

1. **The tree holds no work** — no modified, untracked or ignored file (review
   scratch counts), except regenerable caches, the root `.venv/` and `.tmp/`,
   which has its own guard.
2. **Its git metadata** (HEAD, index, reflog, lock) has not moved for 72 h —
   three days outlast a weekend pause. `WORKTREE_GC_OWNERLESS_IDLE_HOURS`
   overrides the default.

The lock is lifted only if the tree is removed.

## Lock shapes that are never reclaimed

Any lock without a checkable pid — several `(pid`, a value past 4194304, a
hand-made lock — is never reclaimed. A lock with a real pid marks the tree in
use for `worktree-gc` and molt while that pid lives; `worktree-gc` reclaims it
once the pid is dead (it parses `(pid N` from the reason).
