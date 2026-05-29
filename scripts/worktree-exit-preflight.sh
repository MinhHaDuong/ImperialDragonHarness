#!/usr/bin/env bash
set -euo pipefail
# Refuse to exit a worktree that still has uncommitted state.
#
# Why: ExitWorktree is a harness tool, not a Bash command, so the
# `Bash(git worktree remove*)` PreToolUse matcher cannot guard it. A sweep that
# Write's a new ticket draft (untracked, never `git add`'d) and then calls
# ExitWorktree will silently destroy the draft — the failure mode that lost
# the 0173 ticket. See ticket 0174.
#
# This is a skill-level gate, called from /celebrate step 9 and /end-session
# step 7 before invoking ExitWorktree. Checks tracked-modified, staged, AND
# untracked entries — `git status --porcelain` covers all three by default.
#
# Arg: worktree path (default: current directory).
# Exit 0 silently when clean. Exit 1 with a listing on stderr when dirty.

path="${1:-.}"
[ -d "$path" ] || { echo "worktree-exit-preflight: not a directory: $path" >&2; exit 2; }

# -uall expands untracked directories so each lost file is named in the message
# (the failure mode was a single .erg file inside an otherwise-untracked dir).
status=$(git -C "$path" status --porcelain --untracked-files=all 2>/dev/null || true)
[ -z "$status" ] && exit 0

cat >&2 <<EOF
Blocked: worktree '$path' has uncommitted state — ExitWorktree would destroy it.

$status

Commit (and push) anything you mean to keep before calling ExitWorktree. For
ticket drafts filed during /celebrate sweeps, finish the /ticket-new commit
step. For genuine WIP, salvage:

  ~/.claude/scripts/worktree-salvage.sh "$path"

See ticket 0174.
EOF
exit 1
