#!/usr/bin/env bash
# Tests for scripts/bash-env.sh — provenance protection of the
# GUARD_ALLOW_PRIMARY_EDIT escape hatch (ticket 0323, residual 2).
#
# The guard scripts/pretooluse-worktree-path-guard.sh honours
# GUARD_ALLOW_PRIMARY_EDIT as a human-only, pre-session escape hatch. The guard
# hook runs as a bash subprocess with BASH_ENV=scripts/bash-env.sh, so bash-env.sh
# is sourced into the guard's environment. bash-env.sh sources a project `.env`
# under `set -a` (auto-export). An agent can write a `.env` inside its OWN worktree
# (an ordinary, unblocked write); without a provenance snapshot that value would
# be auto-exported into the guard's environment and self-authorize a
# primary-checkout write. bash-env.sh must therefore let only a value present
# BEFORE it ran (the session/systemd launch env) survive.
#
# Both directions are required. A naive "always unset GUARD_ALLOW_PRIMARY_EDIT"
# fix passes (a) but breaks (b) — the real human escape hatch.
#
# NEVER source the real ~/.claude/.env here (it holds secrets): HOME is pointed
# at an empty temp dir so bash-env.sh's user-level source is skipped, and the
# project .env contains ONLY the one guard variable under test.
set -euo pipefail

cd "$(dirname "$0")/.."
BASHENV="$PWD/scripts/bash-env.sh"
fail=0

_tmphome=$(mktemp -d)          # empty HOME → no ~/.claude/.env to source
_projdir=$(mktemp -d)          # stands in for the agent's worktree cwd
printf 'GUARD_ALLOW_PRIMARY_EDIT=1\n' > "$_projdir/.env"

# Drive bash-env.sh the way the guard hook receives it: BASH_ENV points at the
# script, so a fresh non-interactive `bash -c` sources it exactly once at startup
# (an explicit re-source would collide with the session's own ambient BASH_ENV).
# cd into $_projdir so PWD — which bash-env.sh keys on for the project .env — is
# the .env's dir. HOME points at an empty dir so the user-level ~/.claude/.env
# source is skipped. -u BASH_ENV first clears any inherited value; the trailing
# BASH_ENV="$BASHENV" then sets the one under test.
_report='echo "${GUARD_ALLOW_PRIMARY_EDIT:-UNSET}"'

# (a) No prior value; project .env sets =1 → must NOT survive (dropped).
got=$( cd "$_projdir" && env -u GUARD_ALLOW_PRIMARY_EDIT -u BASH_ENV \
        HOME="$_tmphome" BASH_ENV="$BASHENV" bash -c "$_report" )
if [ "$got" = "UNSET" ]; then
    echo "PASS: agent-set project .env GUARD_ALLOW_PRIMARY_EDIT does not survive sourcing"
else
    echo "FAIL: expected UNSET (dropped) for project-only guard var; got: '$got'"
    fail=1
fi

# (b) Genuine prior value (inherited launch env) + project .env also sets it →
# the prior value MUST survive (the real human escape hatch).
got=$( cd "$_projdir" && env -u BASH_ENV \
        GUARD_ALLOW_PRIMARY_EDIT=1 HOME="$_tmphome" BASH_ENV="$BASHENV" bash -c "$_report" )
if [ "$got" = "1" ]; then
    echo "PASS: pre-session GUARD_ALLOW_PRIMARY_EDIT survives sourcing"
else
    echo "FAIL: expected '1' (preserved) for inherited-env guard var; got: '$got'"
    fail=1
fi

rm -r "$_tmphome" "$_projdir"
exit $fail
