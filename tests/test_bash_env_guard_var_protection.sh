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
# Combined report over the FULL guard-trusted var set: the escape hatch plus the
# two test-only root overrides the guard trusts unconditionally (ticket 0323
# REROLL). Setting both _GUARD_*_ROOT to matching bogus values disarms the guard
# for every path, so they need the same provenance protection as the escape hatch.
_report_all='echo "GAPE=${GUARD_ALLOW_PRIMARY_EDIT:-UNSET};WT=${_GUARD_WORKTREE_ROOT:-UNSET};PR=${_GUARD_PRIMARY_ROOT:-UNSET}"'

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

# (c) Forged OLD bookkeeping. The first 0323 fix snapshotted with STATIC,
# committed names (_be_guard_had / _be_guard_val). Because `.env` is sourced as
# bash, a static file could set those exact names and forge the snapshot, so the
# restore re-exported GUARD_ALLOW_PRIMARY_EDIT=1 without the `.env` ever naming
# it. With unforgeable (per-process-nonce) bookkeeping the forgery is inert: the
# variable was absent from the launch env, so it must come back UNSET.
printf 'GUARD_ALLOW_PRIMARY_EDIT=1\n_be_guard_had=1\n_be_guard_val=1\n' > "$_projdir/.env"
got=$( cd "$_projdir" && env -u GUARD_ALLOW_PRIMARY_EDIT -u BASH_ENV \
        HOME="$_tmphome" BASH_ENV="$BASHENV" bash -c "$_report" )
if [ "$got" = "UNSET" ]; then
    echo "PASS: forged static bookkeeping (_be_guard_had/_be_guard_val) cannot resurrect GUARD_ALLOW_PRIMARY_EDIT"
else
    echo "FAIL: forged static bookkeeping smuggled GUARD_ALLOW_PRIMARY_EDIT back; expected UNSET, got: '$got'"
    fail=1
fi

# (d) The two test-only root overrides, set only in a project .env, must NOT
# survive — an agent that sets both to matching bogus values otherwise disarms
# the guard for every path (ticket 0323 REROLL, blocker 2).
printf '_GUARD_WORKTREE_ROOT=/nonexistent\n_GUARD_PRIMARY_ROOT=/nonexistent\n' > "$_projdir/.env"
got=$( cd "$_projdir" && env -u _GUARD_WORKTREE_ROOT -u _GUARD_PRIMARY_ROOT -u BASH_ENV \
        HOME="$_tmphome" BASH_ENV="$BASHENV" bash -c "$_report_all" )
if [ "$got" = "GAPE=UNSET;WT=UNSET;PR=UNSET" ]; then
    echo "PASS: agent-set project .env _GUARD_*_ROOT overrides do not survive sourcing"
else
    echo "FAIL: expected all UNSET for agent-set root overrides; got: '$got'"
    fail=1
fi

# (e) Genuine pre-session (launch env) root overrides MUST survive even when a
# project .env also sets them — the legitimate test-override mechanism. The
# launch value wins; the .env value is dropped.
printf '_GUARD_WORKTREE_ROOT=/env-bogus\n_GUARD_PRIMARY_ROOT=/env-bogus\n' > "$_projdir/.env"
got=$( cd "$_projdir" && env -u BASH_ENV \
        _GUARD_WORKTREE_ROOT=/launch/wt _GUARD_PRIMARY_ROOT=/launch/pr \
        HOME="$_tmphome" BASH_ENV="$BASHENV" bash -c "$_report_all" )
if [ "$got" = "GAPE=UNSET;WT=/launch/wt;PR=/launch/pr" ]; then
    echo "PASS: pre-session _GUARD_*_ROOT overrides survive sourcing (test-override mechanism intact)"
else
    echo "FAIL: expected inherited root overrides preserved; got: '$got'"
    fail=1
fi

rm -r "$_tmphome" "$_projdir"
exit $fail
