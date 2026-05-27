#!/usr/bin/env bash
set -euo pipefail
# GC stale agent worktrees: remove worktrees named agent-* whose branch is
# gone from origin (squash-merged + remote-deleted) AND have no uncommitted
# changes. Never touches dirty worktrees, never uses rm -rf, idempotent.
# Relies on the caller having run `git fetch --prune` first (housekeeping /
# celebrate do). Optional arg: repo dir (default: current dir). See ticket 0169.

repo="${1:-.}"
removed=0
skipped_wip=0

path=""
branch=""

flush() {
    [ -z "$path" ] && return
    local base
    base=$(basename "$path")
    case "$base" in
        agent-*) ;;
        *) path=""; branch=""; return ;;
    esac
    # Never touch a worktree with uncommitted changes (could be user WIP).
    if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
        echo "worktree-gc: skip $base (uncommitted WIP)"
        skipped_wip=$((skipped_wip + 1))
        path=""; branch=""; return
    fi
    if [ -z "$branch" ]; then path=""; branch=""; return; fi
    # 'gone' = the branch had an upstream that no longer exists (merged + pruned).
    local track
    track=$(git -C "$repo" for-each-ref --format='%(upstream:track)' "refs/heads/$branch" 2>/dev/null || true)
    if [ "$track" = "[gone]" ]; then
        git -C "$repo" worktree unlock "$path" 2>/dev/null || true
        if git -C "$repo" worktree remove "$path" 2>/dev/null; then
            echo "worktree-gc: removed $base (branch '$branch' gone)"
            removed=$((removed + 1))
        else
            echo "worktree-gc: could not remove $base — left in place" >&2
        fi
    fi
    path=""; branch=""
}

while IFS= read -r line; do
    case "$line" in
        "worktree "*) flush; path="${line#worktree }" ;;
        "branch refs/heads/"*) branch="${line#branch refs/heads/}" ;;
        "") flush ;;
    esac
done < <(git -C "$repo" worktree list --porcelain)
flush

if [ "$removed" -eq 0 ] && [ "$skipped_wip" -eq 0 ]; then
    exit 0   # nothing to GC — stay silent
fi
echo "worktree-gc: removed $removed, skipped $skipped_wip with WIP."
exit 0
