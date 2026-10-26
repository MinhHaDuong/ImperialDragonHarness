#!/usr/bin/env bash
set -euo pipefail
# GC stale worktrees: remove any registered worktree (regardless of path or
# name — including ones outside .claude/worktrees/, e.g. a stranded /tmp
# worktree) when ALL safety rails pass: the tree is clean (no uncommitted
# changes), its branch is upstream-gone (merged + remote-deleted), it is
# not the worktree this script is invoked from, it is not locked (a lock
# with a live pid or no checkable pid — none, pid 1, several, or past
# pid_max — stays untouched, with two exceptions: a lock whose single pid
# > 1 is dead is unlocked so the rails can proceed, and a harness lock
# naming no owner on a tree with no work in it (ignored files included;
# regenerable caches and the root .venv/ are disposable) whose git metadata
# has sat idle for $WORKTREE_GC_OWNERLESS_IDLE_HOURS (default 72) is
# lifted just before removal and put back if the removal fails), and no live
# process has its cwd inside it. If the live-cwd scan reads nothing at all
# (no python3, no /proc), nothing is removed. The last two rails
# exist because "branch merged + tree clean" is the NORMAL state of a live
# session between turns, not proof of abandonment: on 2026-07-13 this
# script removed two worktrees that were live sessions' base cwds (their
# checked-out branches had merged and deleteBranchOnMerge pruned the
# remotes), stranding those sessions in unregistered husk dirs where git
# resolves to the primary checkout (ticket 0355). A lock is an in-use
# marker (molt's active-session guard reads it that way) — never
# unlock-and-remove blindly; a dead-pid (> 1) lock is the one stale-marker
# exception (2026-09-28, see the lock rail in flush()). A live process cwd
# inside the tree is an active session: the claude CLI holds its cwd at the
# session base for the session's life. `git worktree remove` only detaches
# the worktree — branches and commits survive — and we never rm -rf, so a
# mistaken removal loses no history. Idempotent. Relies on the caller having
# run `git fetch --prune` first (housekeeping / molt do).
# Also report-only surfaces "husk" dirs under .claude/worktrees/ — directories
# that are no longer registered worktrees (a session base cwd deregistered
# mid-session) — which the registered pass cannot see. Husks are never removed
# (may be a live session's base cwd); see ticket 0325.
# Optional arg: repo dir (default: current dir). See tickets 0169, 0195, 0325.

repo="${1:-.}"
removed=0
skipped_wip=0
skipped_locked=0
skipped_live=0
husks=0
declare -a registered_paths=()
ownerless_idle_hours="${WORKTREE_GC_OWNERLESS_IDLE_HOURS:-72}"
[[ "$ownerless_idle_hours" =~ ^[0-9]{1,6}$ ]] || ownerless_idle_hours=72
# The two owner-less lock reasons the harness writes (see the lock rail).
legacy_pid1_re='^(hunt t[^[:space:]]+|claude [^[:space:](]+( [^[:space:](]+)?) [(]pid 1([^0-9]|$)'
not_visible_re='^hunt t[^[:space:]]+ [(]owner pid not visible[)]$'

# Hours since a worktree's git metadata last moved: HEAD, index and reflog
# change with every checkout, commit and status refresh; the lock file dates
# the lock. Prints nothing when no file can be read (the caller keeps it).
idle_hours() {
    local gitdir f m newest=0
    gitdir=$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null) || return 0
    for f in HEAD index logs/HEAD locked; do
        m=$(stat -c %Y -- "$gitdir/$f" 2>/dev/null) || continue
        [ "$m" -gt "$newest" ] && newest=$m
    done
    [ "$newest" -gt 0 ] && echo $(( ($(date +%s) - newest) / 3600 ))
    return 0
}

. "$(dirname "${BASH_SOURCE[0]}")/worktree-clean-lib.sh"

# Liveness rail: snapshot every live process's cwd once (Linux /proc), on the
# first removal candidate — a quiet repo never pays for it. One python3 call
# for all entries, not one fork per process: a host with ~10k processes spent
# ~20 s in the per-process loop. Links it cannot read (other users' entries,
# kernel threads) are skipped and the remaining rails still apply.
# NUL-separated so a newline in a path cannot split an entry. It returns fully
# resolved paths, so candidates are realpath'd before comparison.
declare -a live_cwds=()
live_cwds_loaded=0
load_live_cwds() {
    [ "$live_cwds_loaded" -eq 1 ] && return 0
    live_cwds_loaded=1
    # Not `readlink /proc/[0-9]*/cwd`: uutils readlink stops at the first
    # unreadable link (/proc/1/cwd sorts first), so the batch returned no
    # cwd at all and the live-session rail saw nothing (2026-10-23).
    mapfile -d '' -t live_cwds < <(python3 -I -c '
import glob, os, sys
for link in glob.glob("/proc/[0-9]*/cwd"):
    try:
        sys.stdout.write(os.readlink(link) + "\0")
    except OSError:
        pass
' 2>/dev/null || true)
}

path=""
branch=""
locked_flag=0
lock_reason=""

reset() { path=""; branch=""; locked_flag=0; lock_reason=""; }

report_wip() {
    local tree="$1" base="$2" status
    if ! status=$(git -C "$tree" --no-optional-locks status --porcelain --untracked-files=all 2>/dev/null); then
        echo "worktree-gc: skip $base (could not inspect worktree status)" >&2
        skipped_wip=$((skipped_wip + 1))
        return 0
    fi
    [ -z "$status" ] && return 1
    echo "worktree-gc: skip $base (uncommitted WIP)"
    printf 'worktree-gc: WIP in %q: %q\n' "$base" "$status"
    skipped_wip=$((skipped_wip + 1))
    return 0
}

flush() {
    [ -z "$path" ] && return
    local base
    base=$(basename "$path")
    # Never remove the worktree we are running from (covers the race where a
    # live session sits on a just-merged, now-gone branch). git worktree list
    # reports absolute paths; $PWD is absolute, so this compares cleanly.
    if [ "$path" = "$PWD" ]; then reset; return; fi
    if [ -z "$branch" ]; then
        report_wip "$path" "$base" || true
        reset; return
    fi
    # 'gone' = the branch had an upstream that no longer exists (merged + pruned).
    local track
    track=$(git -C "$repo" for-each-ref --format='%(upstream:track)' "refs/heads/$branch" 2>/dev/null || true)
    if [ "$track" != "[gone]" ]; then
        report_wip "$path" "$base" || true
        reset; return
    fi
    # The tree is now a removal candidate. Never remove one that is a live
    # process's cwd: that process is an active session based there, whatever
    # its branch's upstream says (checked only past the [gone] gate so a
    # quiet repo stays silent — live worktrees on live branches say nothing).
    local rpath lc
    load_live_cwds
    # This script's own cwd is always readable, so an empty list means the
    # scan failed (no python3, unreadable /proc), not that nothing is live.
    if [ "${#live_cwds[@]}" -eq 0 ]; then
        echo "worktree-gc: skip $base (live-cwd scan read nothing — cannot rule out an active session)" >&2
        skipped_live=$((skipped_live + 1))
        reset; return
    fi
    rpath=$(realpath "$path" 2>/dev/null || echo "$path")
    for lc in "${live_cwds[@]:-}"; do
        [ -z "$lc" ] && continue
        case "$lc" in
            "$rpath"|"$rpath"/*)
                echo "worktree-gc: skip $base (live process cwd inside — active session)"
                skipped_live=$((skipped_live + 1))
                reset; return
                ;;
        esac
    done
    # A locked worktree is in use by default — the lock is the in-use
    # marker molt's active-session guard reads. Never unlock-and-remove
    # blindly (the pre-0355 behavior, which defeated the marker). But the
    # harness's own locks carry the owning session's pid in the reason
    # ("claude <name> (pid <N> ...)"), and a lock whose pid is dead is a
    # stale marker, not an active session: unlock it so the remaining rails
    # decide (2026-09-28: a locked tree under a pid dead for days held the
    # last on-disk copy of purged T2 memory; the lock blocked every GC
    # pass). A lock with no checkable pid is an opaque in-use marker, except
    # the two harness owner-less shapes below.
    local unlock_at_removal=0 stale_why=""
    if [ "$locked_flag" -eq 1 ]; then
        # Exactly one `(pid N` with N at most 4194304 (the Linux pid_max
        # ceiling); a second group or an out-of-range number reads as no
        # recorded pid, never as a dead one.
        local lock_pid=""
        if [[ "$lock_reason" =~ \(pid\ ([0-9]{1,7})([^0-9]|$) ]] &&
           [[ "${lock_reason#*"(pid"}" != *"(pid"* ]]; then
            lock_pid=$((10#${BASH_REMATCH[1]}))
            [ "$lock_pid" -le 4194304 ] || lock_pid=""
        fi
        # Pid 1 names no owner either: `$PPID` reads 1 inside a pid
        # namespace (a sandboxed runtime), whose session may still be live
        # and invisible to the live-cwd rail. The harness writes two such
        # shapes, `hunt t<id> (pid 1` or `claude <name> [<name>] (pid 1`
        # (legacy, digit-exact) and hunt's whole reason `hunt t<id> (owner
        # pid not visible)`; those are reclaimed once the tree's git metadata
        # has sat idle past the threshold, the tree is clean by
        # ownerless_tree_clean (so a quiet session editing without git keeps
        # it) and every later rail passes. Any other lock without a checkable
        # pid (several groups, past pid_max, pid 0, `(pid 01)`, hand-made)
        # stays opaque.
        stale_why="pid $lock_pid dead"
        if [ -z "$lock_pid" ] || [ "$lock_pid" -le 1 ]; then
            local idle=""
            if [[ "$lock_pid" = 1 && "$lock_reason" =~ $legacy_pid1_re ]] ||
               [[ -z "$lock_pid" && "$lock_reason" =~ $not_visible_re ]]; then
                idle=$(idle_hours "$path")
                if [ -z "$idle" ] || ! [ "$idle" -ge "$ownerless_idle_hours" ]; then
                    echo "worktree-gc: skip $base (locked, no visible owner${idle:+, idle ${idle}h < ${ownerless_idle_hours}h} — treated as in use)"
                    skipped_locked=$((skipped_locked + 1))
                    reset; return
                fi
                if ! ownerless_tree_clean "$path"; then
                    echo "worktree-gc: skip $base (locked, no visible owner, idle ${idle}h, tree not clean — treated as in use)"
                    skipped_locked=$((skipped_locked + 1))
                    reset; return
                fi
                stale_why="no visible owner, idle ${idle}h"
                unlock_at_removal=1
            else
                echo "worktree-gc: skip $base (locked${lock_pid:+, pid $lock_pid names no owner} — treated as in use)"
                skipped_locked=$((skipped_locked + 1))
                reset; return
            fi
        elif ps -p "$lock_pid" -o pid= >/dev/null 2>&1; then
            echo "worktree-gc: skip $base (locked, pid $lock_pid live — active session)"
            skipped_locked=$((skipped_locked + 1))
            reset; return
        fi
    fi
    if [ "$locked_flag" -eq 1 ] && [ "$unlock_at_removal" -eq 0 ]; then
        if ! git -C "$repo" worktree unlock "$path" 2>/dev/null; then
            echo "worktree-gc: skip $base (lock $stale_why, unlock failed)" >&2
            skipped_locked=$((skipped_locked + 1))
            reset; return
        fi
        echo "worktree-gc: unlocked $base (lock $stale_why — stale marker)"
    fi
    # The worktree owns its ignored .tmp/ tree. Never purge it independently:
    # inspect common exclusion, tracked content, integration ancestry, citation
    # sources, and size before ordinary worktree removal. Run this before the
    # legacy .panel cleanup so a verdict citation remains readable.
    if [ -e "$path/.tmp" ] || [ -L "$path/.tmp" ]; then
        local tmp_guard_rc=0 tmp_guard_out
        tmp_guard_out=$(python3 "$(dirname "$0")/worktree-tmp-guard.py" removal "$repo" "$path" --branch "$branch") || tmp_guard_rc=$?
        [ -z "$tmp_guard_out" ] || printf '%s\n' "$tmp_guard_out"
        if [ "$tmp_guard_rc" -ne 0 ]; then
            if [ "$tmp_guard_rc" -eq 1 ]; then
                echo "worktree-gc: skip $base (.tmp citation found — retained)"
            else
                echo "worktree-gc: skip $base (.tmp safety evidence unavailable — retained)" >&2
            fi
            skipped_wip=$((skipped_wip + 1))
            reset; return
        fi
    fi
    # Only a gone, inactive tree reaches this point, unlocked or holding an
    # owner-less lock that passed its idle and clean checks. The review
    # commands own these two scratch paths; clear them before the WIP check,
    # while retaining every other uncommitted file as a removal blocker.
    # A tracked file under either path may contain real edits; never erase it.
    # Also do not follow a symlinked build/ parent outside the worktree.
    local tracked_panel tracked_base
    if ! tracked_panel=$(git -C "$path" ls-files -- .panel 2>/dev/null) ||
       ! tracked_base=$(git -C "$path" ls-files -- build/panel-head 2>/dev/null); then
        echo "worktree-gc: skip $base (could not inspect review scratch)" >&2
        skipped_wip=$((skipped_wip + 1))
        reset; return
    fi
    if [ -z "$tracked_panel" ]; then
        rm -rf -- "$path/.panel"
    fi
    if [ ! -L "$path/build" ] && [ -z "$tracked_base" ]; then
        rm -rf -- "$path/build/panel-head"
    fi
    if report_wip "$path" "$base"; then
        reset; return
    fi
    # An owner-less lock is lifted only now, after every rail passed, and put
    # back if the removal fails. Concurrent re-locking within this window is
    # not guarded: no harness flow re-locks an idle, branch-gone tree.
    if [ "$unlock_at_removal" -eq 1 ]; then
        if ! git -C "$repo" worktree unlock "$path" 2>/dev/null; then
            echo "worktree-gc: skip $base (lock $stale_why, unlock failed)" >&2
            skipped_locked=$((skipped_locked + 1))
            reset; return
        fi
        echo "worktree-gc: unlocked $base (lock $stale_why — stale marker)"
    fi
    if git -C "$repo" worktree remove "$path" 2>/dev/null; then
        echo "worktree-gc: removed $base (branch '$branch' gone)"
        removed=$((removed + 1))
    else
        echo "worktree-gc: could not remove $base — left in place" >&2
        if [ "$unlock_at_removal" -eq 1 ]; then
            git -C "$repo" worktree lock --reason "$lock_reason" "$path" 2>/dev/null || true
        fi
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
        "locked")
            locked_flag=1
            lock_reason=""
            ;;
        "locked "*)
            locked_flag=1
            lock_reason="${line#locked }"
            ;;
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
# (invocation-invariant, hardened by ticket 0297 — no dependency on
# `git worktree list` output ordering).
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

if [ "$removed" -eq 0 ] && [ "$skipped_wip" -eq 0 ] && [ "$skipped_locked" -eq 0 ] && [ "$skipped_live" -eq 0 ] && [ "$husks" -eq 0 ]; then
    exit 0   # nothing to GC — stay silent
fi
summary="worktree-gc: removed $removed, skipped $skipped_wip with WIP, $skipped_locked locked, $skipped_live live."
if [ "$husks" -gt 0 ]; then
    summary="$summary $husks husk(s) reported (not removed)."
fi
echo "$summary"
exit 0
