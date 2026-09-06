#!/usr/bin/env bash
# Sync the local default branch (main/master) to origin, safely, from any
# checkout or linked worktree of the repo.
#
# Usage: sync-local-main.sh [checkout-dir] [branch]
#   checkout-dir  any checkout/worktree of the repo (default: .)
#   branch        branch to sync (default: detected default branch) — for
#                 repos whose integration branch is not main/master (ticket 0277)
#
# Guarantees (see rules/git.md § Local main syncs eagerly):
# - only the named/default branch moves — never whatever branch happens to be
#   checked out where the script runs;
# - fast-forward only: a diverged local default branch is reported, not moved;
# - no working tree is discarded or stashed: when the default branch is
#   checked out somewhere with conflicting local state, it is left untouched
#   and reported.
#
# Always exits 0 (fit for hooks): staleness is reported on stdout, never
# escalated to a failure that would break a session start or a merge flow.
set -euo pipefail

cd "${1:-.}" 2>/dev/null || { echo "sync-local-main: no such directory '${1:-.}' — skipped"; exit 0; }

git rev-parse --git-common-dir >/dev/null 2>&1 || { echo "sync-local-main: not a git repo — skipped"; exit 0; }
git remote get-url origin >/dev/null 2>&1 || { echo "sync-local-main: no origin remote — nothing to sync"; exit 0; }

# Branch to sync: explicit second argument, else the default branch from
# origin/HEAD, falling back to main, then master.
default="${2:-}"
if [ -z "$default" ]; then
    default=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||') || true
fi
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

# Name the state that actually refused the fast-forward, instead of the old
# "dirty or busy checkout" catch-all (ticket 0851).
#
# git has already stated why it refused, so `$err` is established evidence and
# a local probe of the checkout is only an inference. Classify from `$err`
# first; a checkout can be dirty in ways that have nothing to do with the
# refusal, and an inference that outranks the evidence reports a non-cause
# (reroll 1: an unrelated tracked edit displaced a real path collision, sending
# the operator to back up a file that was never in the way). Three outcomes:
#   - untracked/incoming path collision: git's own refusal, reported with the
#     colliding paths. Untracked files do NOT block a fast-forward in general —
#     the sync is attempted regardless and succeeds when nothing collides — so
#     folding this case into "dirty" told the operator to clean a checkout that
#     did not need cleaning;
#   - tracked modifications: taken when git's refusal names local changes, and
#     as the fallback reading when git's message identifies nothing and the
#     checkout is in fact dirty. This is the one state the operator must deal
#     with by hand;
#   - anything else (a concurrent session's index.lock, a hook, a permission
#     error): git's own first line, verbatim. A guess here is worse than a
#     quotation, since the whole defect was a message that named a cause it had
#     not established.
# The merge runs under LC_ALL=C so this classification reads git's English
# messages on a French desktop as well as in CI.
# Each cause carries its own remedy: the old single tail ("back up the dirty
# file") is wrong advice for a checkout that is merely busy.

# True only on exit 1 — dirty tracked files. `git diff --quiet` also exits >1
# when git itself failed (permission denied, corrupt index), which is evidence
# of nothing and must not be folded into "dirty" (rules/coding-bash.md).
tracked_dirty() {
    local rc=0
    git -C "$1" diff --quiet HEAD 2>/dev/null || rc=$?
    [ "$rc" -eq 1 ]
}

refusal_cause() {
    local dir="$1" err="$2" paths line
    if [[ "$err" == *"untracked working tree file"* ]]; then
        paths=$(printf '%s\n' "$err" \
            | sed -n 's/^[[:space:]][[:space:]]*//p' | head -3 \
            | tr '\n' ' ' | sed 's/[[:space:]]*$//')
        printf '%s' "an untracked file collides with the incoming $default: ${paths:-path not reported by git} — move it aside, then re-run"
    elif [[ "$err" == *"local changes to the following files would be overwritten"* ]] \
         || [[ "$err" == *"Please commit your changes or stash them"* ]] \
         || tracked_dirty "$dir"; then
        # Name the files. An isolated session cannot run `git -C <primary>
        # status` itself (the worktree path guard refuses reads too), so this
        # line is the only diagnostic it gets; "dirty" without a path is what
        # sent one session inferring the set from a stale snapshot.
        paths=$(git -C "$dir" diff --name-only HEAD 2>/dev/null | head -3 | tr '\n' ' ' | sed 's/[[:space:]]*$//')
        printf '%s' "tracked modifications in the checkout: ${paths:-paths unavailable} — back them up, sync, re-apply (rules/git.md)"
    else
        line=$(printf '%s\n' "$err" | grep -v '^[[:space:]]*$' | head -1)
        printf '%s' "git refused: ${line:-no message} — nothing to clean here, re-run once the checkout is free"
    fi
}

# Where (if anywhere) is the default branch checked out? Refs are shared
# across worktrees, so one sync covers them all.
#
# `git worktree list --porcelain` is a live output-rewrite target: a
# framing/summarising hook can inject banner lines into its stdout. Parse
# defensively so such lines cannot corrupt the checkout-location extraction:
#   - grep keeps only lines that begin with a porcelain record key, dropping
#     any injected banner (e.g. "--- Changes ---"); `|| true` keeps the empty
#     result from tripping pipefail;
#   - the awk requires exactly two fields on a `branch` record (NF == 2), so a
#     malformed, extra-field summary line ("branch refs/heads/main is stale")
#     cannot satisfy the ref match and double-emit a path.
# Porcelain paths may contain spaces, so the `worktree` line keeps substr and no
# arity check. (ticket 0333)
co_path=$(git worktree list --porcelain 2>/dev/null \
    | { grep -E '^(worktree |HEAD |branch |detached$|bare$|$)' || true; } \
    | awk -v ref="refs/heads/$default" \
        '$1 == "worktree" { path = substr($0, 10) } $1 == "branch" && NF == 2 && $2 == ref { print path }')

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
elif ff_err=$(LC_ALL=C git -C "$co_path" merge --ff-only --quiet "origin/$default" 2>&1 >/dev/null); then
    echo "sync-local-main: $default fast-forwarded at $co_path ($local_sha -> $remote_sha)"
else
    echo "sync-local-main: could not fast-forward $default at $co_path, left untouched — $(refusal_cause "$co_path" "$ff_err")"
fi
exit 0
