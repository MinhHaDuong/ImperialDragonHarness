#!/usr/bin/env bash
# Sync the local default branch (main/master) to origin, safely, from any
# checkout or linked worktree of the repo.
#
# Guarantees (see rules/git.md § Local main syncs eagerly):
# - only the default branch moves — never whatever branch happens to be
#   checked out where the script runs;
# - fast-forward only: a diverged local default branch is reported, not moved;
# - no working tree is discarded or stashed: when the default branch is
#   checked out somewhere with conflicting local state, it is left untouched
#   and reported.
#
# Always exits 0 (fit for hooks): staleness is reported on stdout, never
# escalated to a failure that would break a session start or a merge flow.
set -euo pipefail

cd "${1:-.}"

git rev-parse --git-common-dir >/dev/null 2>&1 || { echo "sync-local-main: not a git repo — skipped"; exit 0; }
git remote get-url origin >/dev/null 2>&1 || { echo "sync-local-main: no origin remote — nothing to sync"; exit 0; }

# Default branch from origin/HEAD; fall back to main, then master.
default=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||') || true
if [ -z "${default:-}" ]; then
    if git show-ref --verify --quiet refs/heads/main; then default=main
    elif git show-ref --verify --quiet refs/heads/master; then default=master
    else echo "sync-local-main: no origin/HEAD and no local main/master — skipped"; exit 0
    fi
fi
git show-ref --verify --quiet "refs/heads/$default" || { echo "sync-local-main: no local branch '$default' — skipped"; exit 0; }

git fetch --quiet origin "$default" || { echo "sync-local-main: fetch failed (offline?) — skipped"; exit 0; }

local_sha=$(git rev-parse "refs/heads/$default")
remote_sha=$(git rev-parse "refs/remotes/origin/$default")
if [ "$local_sha" = "$remote_sha" ]; then
    exit 0
fi

if ! git merge-base --is-ancestor "refs/heads/$default" "refs/remotes/origin/$default"; then
    echo "sync-local-main: local $default has diverged from origin/$default — left untouched"
    exit 0
fi

# Where (if anywhere) is the default branch checked out? Refs are shared
# across worktrees, so one sync covers them all.
co_path=$(git worktree list --porcelain | awk -v ref="refs/heads/$default" \
    '$1 == "worktree" { path = substr($0, 10) } $1 == "branch" && $2 == ref { print path }')

if [ -z "$co_path" ]; then
    # Not checked out anywhere: ff-update the ref from the remote-tracking
    # ref line 32 already fetched — fetching from "." costs no second network
    # round-trip, and fetch still refuses non-ff and checked-out targets, so
    # this can never clobber anything.
    if git fetch --quiet . "refs/remotes/origin/$default:refs/heads/$default"; then
        echo "sync-local-main: $default updated by ref $local_sha -> $remote_sha"
    else
        echo "sync-local-main: ref update of $default refused — left untouched"
    fi
elif git -C "$co_path" merge --ff-only --quiet "origin/$default" >/dev/null 2>&1; then
    echo "sync-local-main: $default fast-forwarded at $co_path ($local_sha -> $remote_sha)"
else
    echo "sync-local-main: $default checked out at $co_path with conflicting local state — left untouched (back up the dirty file, sync, re-apply; rules/git.md)"
fi
exit 0
