#!/usr/bin/env bash
set -euo pipefail
# GC stale worktrees: remove any registered worktree (regardless of path or
# name — including ones outside .claude/worktrees/, e.g. a stranded /tmp
# worktree) when ALL safety rails pass: the tree is clean (no uncommitted
# changes), its branch is upstream-gone (merged + remote-deleted), and it is
# not the worktree this script is invoked from. `git worktree remove` only
# detaches the worktree — branches and commits survive — and we never rm -rf,
# so a mistaken removal loses no history. Idempotent. Relies on the caller
# having run `git fetch --prune` first (housekeeping / celebrate do).
# Optional arg: repo dir (default: current dir). See tickets 0169, 0195.

repo="${1:-.}"
removed=0
skipped_wip=0
skipped_locked=0

path=""
branch=""
locked_flag=0

reset() { path=""; branch=""; locked_flag=0; }

flush() {
    [ -z "$path" ] && return
    local base
    base=$(basename "$path")
    # Never remove the worktree we are running from (covers the race where a
    # live session sits on a just-merged, now-gone branch). git worktree list
    # reports absolute paths; $PWD is absolute, so this compares cleanly.
    if [ "$path" = "$PWD" ]; then reset; return; fi
    # Never touch a worktree with uncommitted changes (could be user WIP).
    if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
        echo "worktree-gc: skip $base (uncommitted WIP)"
        skipped_wip=$((skipped_wip + 1))
        reset; return
    fi
    if [ -z "$branch" ]; then reset; return; fi
    # 'gone' = the branch had an upstream that no longer exists (merged + pruned).
    local track
    track=$(git -C "$repo" for-each-ref --format='%(upstream:track)' "refs/heads/$branch" 2>/dev/null || true)
    if [ "$track" != "[gone]" ]; then reset; return; fi
    # Locked worktrees: unlock first, then remove. If unlock fails (lock held
    # by another process or by an admin-dir we can't write), skip + report.
    if [ "$locked_flag" -eq 1 ]; then
        if ! git -C "$repo" worktree unlock "$path" 2>/dev/null; then
            echo "worktree-gc: skip $base (lock held — could not unlock)" >&2
            skipped_locked=$((skipped_locked + 1))
            reset; return
        fi
    fi
    if git -C "$repo" worktree remove "$path" 2>/dev/null; then
        echo "worktree-gc: removed $base (branch '$branch' gone)"
        removed=$((removed + 1))
    else
        echo "worktree-gc: could not remove $base — left in place" >&2
    fi
    reset
}

while IFS= read -r line; do
    case "$line" in
        "worktree "*) flush; path="${line#worktree }" ;;
        "branch refs/heads/"*) branch="${line#branch refs/heads/}" ;;
        "locked"|"locked "*) locked_flag=1 ;;
        "") flush ;;
    esac
done < <(git -C "$repo" worktree list --porcelain)
flush

if [ "$removed" -eq 0 ] && [ "$skipped_wip" -eq 0 ] && [ "$skipped_locked" -eq 0 ]; then
    exit 0   # nothing to GC — stay silent
fi
echo "worktree-gc: removed $removed, skipped $skipped_wip with WIP, $skipped_locked locked."
exit 0
