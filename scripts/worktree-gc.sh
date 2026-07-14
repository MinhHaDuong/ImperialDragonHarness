#!/usr/bin/env bash
set -euo pipefail
# GC stale worktrees: remove any registered worktree (regardless of path or
# name — including ones outside .claude/worktrees/, e.g. a stranded /tmp
# worktree) when ALL safety rails pass: the tree is clean (no uncommitted
# changes), its branch is upstream-gone (merged + remote-deleted), and it is
# not the worktree this script is invoked from. `git worktree remove` only
# detaches the worktree — branches and commits survive — and we never rm -rf,
# so a mistaken removal loses no history. Idempotent. Relies on the caller
# having run `git fetch --prune` first (housekeeping / roar do).
# Also report-only surfaces "husk" dirs under .claude/worktrees/ — directories
# that are no longer registered worktrees (a session base cwd deregistered
# mid-session) — which the registered pass cannot see. Husks are never removed
# (may be a live session's base cwd); see ticket 0325.
# Optional arg: repo dir (default: current dir). See tickets 0169, 0195, 0325.

repo="${1:-.}"
removed=0
skipped_wip=0
skipped_locked=0
husks=0
declare -a registered_paths=()

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
        "worktree "*) flush; path="${line#worktree }"; registered_paths+=("$path") ;;
        "branch refs/heads/"*)
            # A porcelain branch record is `branch refs/heads/<name>` and a
            # ref name carries no whitespace. Reject a multi-token remainder
            # (e.g. an appended framing banner like
            # `branch refs/heads/main is stale`) so a rewritten/framed line
            # cannot forge a wrong branch value. Fail closed: with no branch
            # set, flush() skips the worktree — never a wrongful removal.
            rest="${line#branch refs/heads/}"
            case "$rest" in
                *[[:space:]]*) ;;   # multi-token → ignore
                *) branch="$rest" ;;
            esac
            ;;
        "locked"|"locked "*) locked_flag=1 ;;
        "") flush ;;
    esac
done < <(git -C "$repo" worktree list --porcelain)
flush

# Husk scan (ticket 0325): a directory under .claude/worktrees/ that is NOT a
# registered git worktree is a "husk" — e.g. a session base cwd deregistered
# mid-session, leaving only a scratch .claude/ subdir behind. git commands run
# inside a husk resolve to the PRIMARY repo, so it is invisible to the porcelain
# pass above and accumulates. Report-only, never removed — PERMANENTLY, not an
# initial cut: a husk may still be a LIVE session's base cwd (the harness
# resets the shell cwd there after every command), and no liveness signal
# closes that gap safely — see ticket 0338 for the investigation that closed
# the removal-heuristic question. We only surface it.
# Root on the PRIMARY repo, not on `git rev-parse --show-toplevel`: when this
# script runs from a linked worktree (the harness's normal cwd — molt/roar
# invoke it bare with repo=".") that would resolve to the worktree's own root,
# whose .claude/worktrees/ is absent, silently skipping the scan.
# `--git-common-dir` points at the shared .git of the primary checkout, so its
# parent IS the primary root — from any worktree, registered or not
# (invocation-invariant; same plumbing idiom as guard-commit-on-main.sh and
# pretooluse-worktree-path-guard.sh, hardened by ticket 0297 — no dependency
# on `git worktree list` output ordering).
git_common_dir=$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
primary_root=""
[ -n "$git_common_dir" ] && primary_root=$(dirname "$git_common_dir")
wtdir="$primary_root/.claude/worktrees"
if [ -n "$primary_root" ] && [ -d "$wtdir" ] && { [ ! -r "$wtdir" ] || [ ! -x "$wtdir" ]; }; then
    # Fail open, but VISIBLY: a `find` that dies on an unreadable dir inside the
    # process substitution below is invisible to `set -e`, so the scan would
    # otherwise report zero husks silently. Signal on stderr, matching the other
    # anomaly lines, and skip the scan.
    echo "worktree-gc: cannot scan $wtdir (unreadable) — husk scan skipped" >&2
elif [ -n "$primary_root" ] && [ -d "$wtdir" ]; then
    # Normalize the registered set ONCE, not per husk: realpath is a fork/exec,
    # and re-resolving m registered paths for each of n husks is O(n*m) spawns
    # where O(n+m) suffices.
    declare -a registered_real=()
    for reg in "${registered_paths[@]:-}"; do
        [ -z "$reg" ] && continue
        registered_real+=("$(realpath "$reg" 2>/dev/null || echo "$reg")")
    done
    while IFS= read -r -d '' dir; do
        rdir=$(realpath "$dir" 2>/dev/null || echo "$dir")
        is_registered=0
        for rreg in "${registered_real[@]:-}"; do
            [ -z "$rreg" ] && continue
            # A dir is NOT a husk when it equals a registered worktree OR is an
            # ancestor of one: a multi-segment name (EnterWorktree allows
            # `g/leaf`) registers `.../g/leaf`, but find -maxdepth 1 only sees the
            # container `g`. An exact-path test would false-flag `g` as a husk and
            # could mislead a human into deleting a live worktree's container.
            if [ "$rdir" = "$rreg" ]; then is_registered=1; break; fi
            case "$rreg" in "$rdir"/*) is_registered=1; break ;; esac
        done
        if [ "$is_registered" -eq 0 ]; then
            # Print with %q so a control char (e.g. a newline) in the dirname
            # cannot forge an extra output line — raw interpolation would split
            # the message and let the name inject a standalone banner-like line.
            printf 'worktree-gc: husk %q — unregistered dir at %q, not GC'\''d (report-only)\n' \
                "$(basename "$dir")" "$dir"
            husks=$((husks + 1))
        fi
    done < <(find "$wtdir" -mindepth 1 -maxdepth 1 -type d -print0)
fi

if [ "$removed" -eq 0 ] && [ "$skipped_wip" -eq 0 ] && [ "$skipped_locked" -eq 0 ] && [ "$husks" -eq 0 ]; then
    exit 0   # nothing to GC — stay silent
fi
summary="worktree-gc: removed $removed, skipped $skipped_wip with WIP, $skipped_locked locked."
if [ "$husks" -gt 0 ]; then
    summary="$summary $husks husk(s) reported (not removed)."
fi
echo "$summary"
exit 0
