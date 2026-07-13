#!/bin/bash
set -euo pipefail
# Block "gh pr merge" inside a git worktree.
# Matcher in settings.json ensures this only runs for "gh pr merge" commands.

cat > /dev/null  # consume stdin

# Identity predicate (ticket 0308): fire only inside a genuine harness worktree,
# not in any directory that merely carries a `.git` gitdir: file. The old
# `[ -f .git ] && grep gitdir:` check blocked ANY such tree — a submodule or an
# ad-hoc worktree — as a false positive on this fail-closed guard. This mirrors
# `in_worktree()` in skills/merge/erg-pr-merge (0301) and
# scripts/guard-worktree-identity.sh: the cwd must sit under
# `.claude/worktrees/<name>` AND `git rev-parse --show-toplevel` must resolve to
# a tree whose basename is that `<name>` and is not the primary root itself.
# (0302 will unify these three copies into a shared helper.)
in_worktree() {
  local cwd top name prefix
  cwd=$(pwd -P)
  prefix=${cwd%%/.claude/worktrees/*}
  name=${cwd#*/.claude/worktrees/}
  name=${name%%/*}
  [ -n "$name" ] || return 1
  top=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
  [ -n "$top" ] || return 1
  [ "$(basename "$top")" = "$name" ] || return 1
  [ "$top" != "$prefix" ] || return 1
  return 0
}

if in_worktree; then
  cat >&2 <<'EOF'
Blocked: gh pr merge fails in git worktrees (main is locked by parent).
Use the GitHub API directly:

  PR=NUMBER
  gh api "repos/{owner}/{repo}/pulls/$PR/merge" -X PUT -f merge_method=squash
  gh api "repos/{owner}/{repo}/pulls/$PR" --jq .head.ref | xargs -I{} git push origin --delete {}
EOF
  exit 2
fi

exit 0
