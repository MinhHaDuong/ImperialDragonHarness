#!/usr/bin/env bash
set -euo pipefail
# Refuse to exit a worktree that still has uncommitted state.
#
# Why: a sweep that Write's a new ticket draft (untracked, never `git add`'d)
# and then leaves its worktree loses the draft — the failure mode that lost
# the 0173 ticket under the runtime's ExitWorktree. See ticket 0174. Plain
# `git worktree remove` refuses too, but without the salvage route below.
#
# This is a skill-level gate, called from /roar step 9 (through
# skills/roar/close-and-clean.sh) and /lair step 7 before leaving the worktree. Checks tracked-modified, staged, AND
# untracked entries — `git status --porcelain` covers all three by default.
#
# Arg: worktree path (default: current directory).
# Exit 0 silently when clean. Exit 1 with a listing on stderr when dirty.

removal=0
branch=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --removal) removal=1; shift ;;
        --branch) [ "$#" -ge 2 ] || exit 2; branch="$2"; shift 2 ;;
        --) shift; break ;;
        -*) echo "worktree-exit-preflight: unknown option: $1" >&2; exit 2 ;;
        *) break ;;
    esac
done
path="${1:-.}"
[ -d "$path" ] || { echo "worktree-exit-preflight: not a directory: $path" >&2; exit 2; }
root=$(git -C "$path" rev-parse --show-toplevel 2>/dev/null) || {
    echo "worktree-exit-preflight: not a Git worktree: $path" >&2
    exit 2
}
if [ "$(realpath "$path")" != "$(realpath "$root")" ]; then
    echo "worktree-exit-preflight: expected worktree root: $path" >&2
    exit 2
fi

# `.tmp/` is ignored by common Git metadata, so status alone cannot protect it.
# Inspect it before any legacy review-scratch cleanup; never delete it here.
preserve_panel=0
if [ -e "$root/.tmp" ] || [ -L "$root/.tmp" ]; then
    mode=preflight
    [ "$removal" -eq 0 ] || mode=removal
    [ "$removal" -eq 1 ] || preserve_panel=1
    args=()
    [ -z "$branch" ] || args+=(--branch "$branch")
    if ! python3 "$(dirname "$0")/worktree-tmp-guard.py" "$mode" "$root" "$root" "${args[@]}"; then
        echo "worktree-exit-preflight: .tmp safety check failed — leaving the worktree in place" >&2
        exit 2
    fi
fi

# Inspect both pathspecs successfully before deleting either one. A failed
# ls-files must never look like an empty tracked set.
tracked_panel=$(git -C "$path" ls-files -- .panel 2>/dev/null) || {
    echo "worktree-exit-preflight: cannot inspect .panel in $path" >&2
    exit 2
}
tracked_base=$(git -C "$path" ls-files -- build/panel-head 2>/dev/null) || {
    echo "worktree-exit-preflight: cannot inspect build/panel-head in $path" >&2
    exit 2
}

# Review reports and the temporary base checkout are command-owned scratch.
# Remove only these named paths, then apply the original complete status gate.
if [ "$preserve_panel" -eq 0 ] && [ -z "$tracked_panel" ]; then
    rm -rf -- "$path/.panel"
fi
if [ ! -L "$path/build" ] && [ -z "$tracked_base" ]; then
    rm -rf -- "$path/build/panel-head"
fi

# -uall expands untracked directories so each lost file is named in the message
# (the failure mode was a single .erg file inside an otherwise-untracked dir).
status=$(git -C "$path" status --porcelain --untracked-files=all 2>/dev/null) || {
    echo "worktree-exit-preflight: cannot inspect worktree status: $path" >&2
    exit 2
}
[ -z "$status" ] && exit 0

cat >&2 <<EOF
Blocked: worktree '$path' has uncommitted state — removing the worktree would destroy it.

$status

Commit (and push) anything you mean to keep before removing the worktree. For
ticket drafts filed during /roar sweeps, commit the new tickets/NNNN-*.erg
(erg new writes it; you must commit it). For genuine WIP, salvage:

  "$(cd -P "$(dirname "$0")" && pwd -P)/worktree-salvage.sh" "$path"

See ticket 0174.
EOF
exit 1
