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
# skills/roar/close-and-clean.sh) and /lair step 7 before leaving the worktree. Checks tracked-modified, staged
# and untracked entries; ignored files are disposable (scripts/worktree-clean-lib.sh, ticket 1500).
#
# --removal and --branch are accepted and ignored (kept so callers need no edit).
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

# Review reports and the temporary base checkout are command-owned scratch:
# the status gate below ignores their untracked (??) records, never a
# staged move or deletion, and they are deleted only once it passes.
# A refused exit keeps them, since a review may have left its only evidence there.
purge_panel=0
if [ -z "$tracked_panel" ]; then purge_panel=1; fi
purge_base=0
if [ ! -L "$path/build" ] && [ -z "$tracked_base" ]; then purge_base=1; fi

# Same residue definition as worktree-gc.sh (shared lib): what plain status
# lists, never ignored files. Untracked directories are expanded so each lost
# file is named in the message (the 0174 failure was one .erg file inside an
# otherwise-untracked dir).
. "$(dirname "${BASH_SOURCE[0]}")/worktree-clean-lib.sh"
status=$(worktree_residue "$path") || {
    echo "worktree-exit-preflight: cannot inspect worktree status: $path" >&2
    exit 2
}
if [ "$purge_panel" -eq 1 ] && [ -n "$status" ]; then
    status=$(printf '%s\n' "$status" | grep -Ev '^\?\? \.panel(/|$)' || true)
fi
if [ "$purge_base" -eq 1 ] && [ -n "$status" ]; then
    status=$(printf '%s\n' "$status" | grep -Ev '^\?\? build/panel-head(/|$)' || true)
fi
if [ -z "$status" ]; then
    if [ "$purge_panel" -eq 1 ]; then rm -rf -- "$path/.panel"; fi
    if [ "$purge_base" -eq 1 ]; then rm -rf -- "$path/build/panel-head"; fi
    exit 0
fi

cat >&2 <<EOF
Blocked: worktree '$path' has uncommitted or untracked state — removing the worktree would destroy it.

$status

Commit (and push) anything you mean to keep before removing the worktree. For
ticket drafts filed during /roar sweeps, commit the new tickets/NNNN-*.erg
(erg new writes it; you must commit it). For genuine WIP, salvage:

  "$(cd -P "$(dirname "$0")" && pwd -P)/worktree-salvage.sh" "$path"

See ticket 0174.
EOF
exit 1
