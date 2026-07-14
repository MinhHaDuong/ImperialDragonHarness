#!/bin/bash
# Loaded via BASH_ENV — sourced at startup of every Claude Code bash subprocess.
# Exports .env secrets into the process environment without inlining them in argv
# (inlining in argv leaks secrets to ps -ef, which is visible to all local users).
#
# BASH_ENV is honored by non-interactive bash (i.e. "bash -c ..."), which is
# exactly what Claude Code uses for Bash tool calls.

set -a  # mark all subsequent assignments for export

# Provenance guard for GUARD_ALLOW_PRIMARY_EDIT (ticket 0323, residual 2). The
# worktree-path guard (scripts/pretooluse-worktree-path-guard.sh) treats this
# variable as a human-only, pre-session escape hatch. That guard runs as a bash
# subprocess with BASH_ENV pointing here, so this script is sourced into its
# environment. Because the `.env` files below are sourced under `set -a`, an
# agent could write a `.env` in its own worktree setting
# GUARD_ALLOW_PRIMARY_EDIT=1 and have it auto-exported into the guard's env,
# self-authorizing a primary-checkout write. Snapshot the pre-sourcing value and
# restore-or-unset it afterwards, so only a value present in the launch
# environment (systemd/shell, before this script ran) survives. Only this one
# variable is protected; all other .env values load unchanged.
if [ -n "${GUARD_ALLOW_PRIMARY_EDIT+x}" ]; then
    _be_guard_had=1
    _be_guard_val=$GUARD_ALLOW_PRIMARY_EDIT
else
    _be_guard_had=0
fi

[ -f "$HOME/.claude/.env" ] && source "$HOME/.claude/.env"

# Project-level .env, identified by PWD (Claude Code sets PWD to the project dir
# for each subprocess). Skip if it resolves to the same file as the user-level one.
if [ -n "${PWD:-}" ] && [ -f "$PWD/.env" ]; then
    _be_proj="$(realpath "$PWD/.env" 2>/dev/null)"
    _be_user="$(realpath "$HOME/.claude/.env" 2>/dev/null)"
    [ "$_be_proj" != "$_be_user" ] && source "$PWD/.env"
    unset _be_proj _be_user
fi

# Restore GUARD_ALLOW_PRIMARY_EDIT to its pre-sourcing provenance (see snapshot
# above). Still under `set -a`, so a restored value keeps its export attribute.
if [ "$_be_guard_had" = 1 ]; then
    GUARD_ALLOW_PRIMARY_EDIT=$_be_guard_val
else
    unset GUARD_ALLOW_PRIMARY_EDIT
fi
unset _be_guard_had _be_guard_val

set +a
