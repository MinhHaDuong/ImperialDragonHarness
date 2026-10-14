# Worktree identity (0310)

To identify a Git worktree, use `git rev-parse --is-inside-work-tree`.
The predicate `[ -f .git ]` is forbidden: it only recognizes linked worktrees
and rejects ordinary Git repositories whose `.git` is a directory.
