#!/usr/bin/env bash
set -euo pipefail
# Salvage uncommitted WIP from a worktree before it is removed.
# Commits everything, then pushes the branch so the work survives the
# worktree's deletion. Safe to run on a clean worktree (no-op).
# See ticket 0168.

usage() { echo "usage: worktree-salvage.sh <worktree-path>" >&2; exit 2; }

path="${1:-}"
[ -z "$path" ] && usage
[ -d "$path" ] || { echo "worktree-salvage: not a directory: $path" >&2; exit 2; }

if [ -z "$(git -C "$path" status --porcelain)" ]; then
    echo "worktree-salvage: nothing to salvage (clean tree) at $path"
    exit 0
fi

git -C "$path" add -A
git -C "$path" commit --quiet -m "WIP: salvaged from interrupted raid"

branch=$(git -C "$path" symbolic-ref --quiet --short HEAD || true)
if [ -z "$branch" ]; then
    echo "worktree-salvage: committed WIP on detached HEAD at $path." >&2
    echo "  HEAD is now $(git -C "$path" rev-parse --short HEAD); create a branch before removing the worktree." >&2
    exit 0
fi

echo "worktree-salvage: committed WIP on branch '$branch'."
if git -C "$path" push --quiet -u origin "$branch"; then
    echo "worktree-salvage: pushed '$branch' to origin — WIP is safe."
else
    echo "worktree-salvage: WARNING — push failed. The WIP commit exists locally on '$branch'" >&2
    echo "  but is NOT on origin yet. Push it manually before deleting the branch." >&2
fi
exit 0
