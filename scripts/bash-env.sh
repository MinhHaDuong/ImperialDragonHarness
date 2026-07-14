#!/bin/bash
# Loaded via BASH_ENV — sourced at startup of every Claude Code bash subprocess.
# Exports .env secrets into the process environment without inlining them in argv
# (inlining in argv leaks secrets to ps -ef, which is visible to all local users).
#
# BASH_ENV is honored by non-interactive bash (i.e. "bash -c ..."), which is
# exactly what Claude Code uses for Bash tool calls.
#
# Provenance protection for guard-trusted variables (ticket 0323, residual 2 +
# REROLL). The worktree-path guard (scripts/pretooluse-worktree-path-guard.sh)
# treats a small set of variables as human-only, pre-session inputs:
#   GUARD_ALLOW_PRIMARY_EDIT  — the escape hatch that disables the deny entirely;
#   _GUARD_WORKTREE_ROOT  \     the test-only root override — if BOTH are set the
#   _GUARD_PRIMARY_ROOT   /     guard trusts them instead of the git-derived
#                              roots, so matching bogus values disarm it for
#                              every path.
# That guard runs as a bash subprocess with BASH_ENV pointing here, so this
# script is sourced into its environment, and the `.env` files below are sourced
# under `set -a` (auto-export). An agent can write a `.env` in its OWN worktree
# (an ordinary, unblocked write); any of these variables set there would be
# auto-exported into the guard's environment and either self-authorize a
# primary-checkout write or silently disarm the guard. Only a value present in
# the launch environment (systemd/shell, before this script ran) may survive; a
# `.env` contribution must be dropped.
#
# The protection covers the FULL trusted set (not just the escape hatch), and its
# bookkeeping is UNFORGEABLE. A prior fix snapshotted with static, committed
# variable names (_be_guard_had / _be_guard_val); because `.env` is sourced as
# bash, a static file could pre-set those exact names and forge the snapshot the
# restore trusts. Here the snapshot variables are suffixed with a per-process
# nonce computed BEFORE any `.env` is sourced, so a statically-written `.env`
# cannot name them. Each trusted var is captured before sourcing and restored to
# its captured value — or unset if it had none — afterwards. All other `.env`
# values load unchanged.

_be_guard_vars='GUARD_ALLOW_PRIMARY_EDIT _GUARD_WORKTREE_ROOT _GUARD_PRIMARY_ROOT'
_be_nonce="$$_${RANDOM}_${RANDOM}_${SRANDOM:-$RANDOM}"

# Snapshot launch-env values into nonce-named scalars. Done before `set -a` so the
# bookkeeping variables themselves are never exported into the guard's env.
for _be_v in $_be_guard_vars; do
    if [ -n "${!_be_v+x}" ]; then
        printf -v "_be_snap_${_be_nonce}_${_be_v}" %s "${!_be_v}"
    fi
done
unset _be_v

set -a  # mark all subsequent assignments for export

[ -f "$HOME/.claude/.env" ] && source "$HOME/.claude/.env"

# Project-level .env, identified by PWD (Claude Code sets PWD to the project dir
# for each subprocess). Skip if it resolves to the same file as the user-level one.
if [ -n "${PWD:-}" ] && [ -f "$PWD/.env" ]; then
    _be_proj="$(realpath "$PWD/.env" 2>/dev/null)"
    _be_user="$(realpath "$HOME/.claude/.env" 2>/dev/null)"
    [ "$_be_proj" != "$_be_user" ] && source "$PWD/.env"
    unset _be_proj _be_user
fi

# Restore each guard-trusted var to its captured launch-env provenance. Still under
# `set -a`, so a restored value keeps its export attribute; an unset drops any
# value a `.env` tried to inject.
for _be_v in $_be_guard_vars; do
    _be_snap="_be_snap_${_be_nonce}_${_be_v}"
    if [ -n "${!_be_snap+x}" ]; then
        printf -v "$_be_v" %s "${!_be_snap}"
    else
        unset "$_be_v"
    fi
    unset "$_be_snap"
done
unset _be_v _be_snap _be_guard_vars _be_nonce

set +a
