#!/bin/bash
set -euo pipefail
# PreToolUse hook: warn when Write/Edit/NotebookEdit targets the main repo
# path during a worktree session. Non-blocking (exit 0) — advisory only.
# See ticket 0171.

input=$(cat)

command -v jq &>/dev/null || exit 0

file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
[ -z "$file_path" ] && exit 0
hook_cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)

# Identity predicate (ticket 0308): a genuine harness worktree, not merely a
# directory carrying a `.git` gitdir: file (a submodule or an ad-hoc worktree
# would satisfy the old `[ -f .git ] && grep gitdir:` check and trip a spurious
# advisory). Mirrors `in_worktree()` in skills/merge/erg-pr-merge (0301) and
# scripts/guard-worktree-identity.sh: the cwd must sit under
# `.claude/worktrees/<name>` AND `git rev-parse --show-toplevel` must resolve to
# a tree whose basename is that `<name>` and is not the primary root itself.
# (0302 will unify these three copies into a shared helper.)
_in_worktree() {
    local cwd top name prefix
    cwd=$(pwd -P)
    prefix=${cwd%%/.claude/worktrees/*}   # enclosing path before the marker
    name=${cwd#*/.claude/worktrees/}      # <name>[/subdir...]
    name=${name%%/*}
    [ -n "$name" ] || return 1
    top=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    [ -n "$top" ] || return 1
    [ "$(basename "$top")" = "$name" ] || return 1
    [ "$top" != "$prefix" ] || return 1
    return 0
}

# Allow env-var overrides for testing without a real git repo
if [ -n "${_GUARD_WORKTREE_ROOT:-}" ] && [ -n "${_GUARD_PRIMARY_ROOT:-}" ]; then
    worktree_root="$_GUARD_WORKTREE_ROOT"
    primary_root="$_GUARD_PRIMARY_ROOT"
elif _in_worktree; then
    worktree_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
    git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null) || exit 0
    primary_root=$(dirname "$git_common_dir")
else
    exit 0
fi

[ "$worktree_root" = "$primary_root" ] && exit 0

# Resolve relative file_path against the PreToolUse JSON's .cwd (the cwd the
# tool will run from), not the hook's own cwd. Fall back to $(pwd) when .cwd
# is absent so older runners and tests that don't supply it still work.
if [ "${file_path#/}" = "$file_path" ]; then
    if [ -n "$hook_cwd" ]; then
        file_path="$hook_cwd/$file_path"
    else
        file_path="$(pwd)/$file_path"
    fi
fi

case "$file_path" in
    "$primary_root"/*)
        case "$file_path" in
            "$worktree_root"/*)
                exit 0  # already inside the worktree
                ;;
        esac
        rel="${file_path#$primary_root/}"
        echo "Worktree path guard: '$rel' resolves to the main repo, not the worktree." >&2
        echo "Did you mean: $worktree_root/$rel" >&2
        ;;
esac

exit 0
