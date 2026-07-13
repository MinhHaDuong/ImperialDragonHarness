#!/bin/bash
set -euo pipefail
# Block "gh pr merge" inside a git worktree.
# Matcher in settings.json ensures this only runs for "gh pr merge" commands.

cat > /dev/null  # consume stdin

# Linked-worktree predicate (ticket 0308): fire in ANY linked git worktree,
# not only harness `.claude/worktrees/<name>` ones. This guard is fail-closed
# and its whole purpose is to stop `gh pr merge`, which git aborts with
# `fatal: 'main' is already used by worktree at ...` in EVERY linked worktree
# (main's ref is locked by the primary checkout) — ad-hoc worktrees included.
# The old `[ -f .git ] && grep gitdir:` check had one real false positive: a
# submodule, whose `.git` gitdir: file points at the SUPERPROJECT but whose own
# ref-store is separate, so it shares no lock. The distinguishing test is
# git-dir vs git-common-dir: in a linked worktree the git-dir is
# `.../worktrees/<name>` under the common dir, so the two DIFFER; in the primary
# checkout and in a submodule the git-dir equals its own common dir, so they are
# EQUAL. This predicate deliberately DIFFERS from the harness-identity predicate
# used by the advisory pretooluse path guard and guard-worktree-identity.sh:
# here we want any linked worktree, not only the named harness ones.
in_worktree() {
  local git_dir common_dir
  git_dir=$(git rev-parse --absolute-git-dir 2>/dev/null) || return 1
  common_dir=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ -n "$git_dir" ] || return 1
  [ -n "$common_dir" ] || return 1
  [ "$git_dir" != "$common_dir" ]
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
