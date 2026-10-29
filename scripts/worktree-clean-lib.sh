#!/usr/bin/env bash
set -euo pipefail
# Sourced by worktree-gc.sh and worktree-exit-preflight.sh: one definition of
# what a worktree may hold and still be removed without losing work.
#
# worktree_residue <path> prints, one per line, every status entry that
# removing the tree would destroy and that is not disposable: anything
# modified, staged or untracked, and any ignored path except regenerable
# caches (the root .venv/, rebuilt from the lock, tool caches anywhere, and
# the *.egg-info/ setuptools rebuilds on every `uv run`) and .tmp/ (its own
# guard decides). Ignored files count: a repo may ignore `*`, and
# `git worktree remove` deletes them. --no-optional-locks keeps the status
# from rewriting the index, which would restart the tree's idle clock.
# Returns 1 when git cannot answer (an unreadable tree is never "clean").
worktree_residue() {
    local out line p
    out=$(git -C "$1" --no-optional-locks status --porcelain=v1 \
        --untracked-files=all --ignored=matching 2>/dev/null) || return 1
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        p="${line:3}"
        case "$line" in
            "!! "*)
                case "/$p" in
                    /.tmp/*|/.venv/*|*/__pycache__/*|*/.pytest_cache/*|*/.ruff_cache/*|*/.mypy_cache/*|*.egg-info/*) continue ;;
                esac ;;
        esac
        printf '%s\n' "$line"
    done <<<"$out"
    return 0
}

# ownerless_tree_clean <path>: true when worktree_residue finds nothing.
ownerless_tree_clean() {
    local residue
    residue=$(worktree_residue "$1") || return 1
    [ -z "$residue" ]
}
