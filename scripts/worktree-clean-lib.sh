#!/usr/bin/env bash
set -euo pipefail
# Sourced by worktree-gc.sh and worktree-exit-preflight.sh: one definition of
# what a worktree may hold and still be removed without losing work.
#
# The residue rule is git's own (ticket 1500): `git worktree remove` without
# --force refuses modified, staged and untracked files and deletes ignored
# ones, so plain status (no --ignored) is the residue. A git-ignored file is
# disposable in every project, a root .venv or build/ included when the
# project or the venv ignores it; an unignored one is untracked work.
#
# worktree_residue <path> prints every status entry, one per line.
# --untracked-files=all names each lost file instead of folding an untracked
# directory into one entry; --no-optional-locks keeps the status from
# rewriting the index, which would restart the tree's idle clock.
# Returns 1 when git cannot answer (an unreadable tree is never "clean").
worktree_residue() {
    local out
    out=$(git -C "$1" --no-optional-locks status --porcelain=v1 \
        --untracked-files=all 2>/dev/null) || return 1
    [ -z "$out" ] || printf '%s\n' "$out"
    return 0
}

# ownerless_tree_clean <path>: true when worktree_residue finds nothing.
ownerless_tree_clean() {
    local residue
    residue=$(worktree_residue "$1") || return 1
    [ -z "$residue" ]
}

# worktree_nested <path>: prints "nested worktree: <path>" for every other
# registered worktree lying inside <path>, dirty or not (no recursion into its
# state). `/.claude/worktrees/` is ignored (ticket 1495), so status calls the
# outer tree clean while `git worktree remove` deletes the inner one with its
# uncommitted work, which is not an ignored file (7eacadd2). Paths are
# canonical and matched on "<tree>/", so /x/a never matches /x/ab.
# Returns 1 when git cannot answer.
worktree_nested() {
    local tree list line wt
    tree=$(cd -P "$1" 2>/dev/null && pwd -P) || return 1
    list=$(git -C "$1" worktree list --porcelain 2>/dev/null) || return 1
    while IFS= read -r line; do
        case "$line" in
            "worktree "*)
                wt=$(cd -P "${line#worktree }" 2>/dev/null && pwd -P) || continue
                case "$wt/" in
                    "$tree/"?*) printf 'nested worktree: %s\n' "$wt" ;;
                esac ;;
        esac
    done <<<"$list"
    return 0
}
