#!/bin/bash
set -euo pipefail
# PreToolUse hook: warn when Write/Edit/NotebookEdit targets the main repo
# path during a worktree session. Non-blocking (exit 0) — advisory only.
# See ticket 0171.

input=$(cat)

command -v jq &>/dev/null || exit 0

file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0

_in_worktree() {
    [ -f .git ] && grep -q "gitdir:" .git 2>/dev/null
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

# Normalize to absolute path
if [ "${file_path#/}" = "$file_path" ]; then
    file_path="$(pwd)/$file_path"
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
