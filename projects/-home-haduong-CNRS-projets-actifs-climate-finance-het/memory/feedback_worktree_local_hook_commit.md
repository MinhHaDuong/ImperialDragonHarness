# DELETED 2026-09-25T16:00Z: feedback_worktree_local_hook_commit
# Reason: The concrete example (ticket 0132, tickets/erg large-file guard) is closed and its literal command now points at a renamed directory (hooks/ was renamed to .githooks/ on 2026-07-16), so following the note verbatim would silently no-op. The underlying technique (override core.hooksPath per-invocation to commit through a fixed hook) is still sound and worth preserving with the corrected path, alongside the sibling entry's hooksPath discussion.
# Original content preserved in git history.
