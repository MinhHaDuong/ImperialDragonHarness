#!/usr/bin/env bash
# Tests for scripts/bash-env.sh — the BASH_ENV shim sourced at the start of every
# Claude Code bash subprocess. It loads two .env sources with DIFFERENT trust:
#
#   * $HOME/.claude/.env  — user-owned, trusted: sourced as shell code.
#   * $PWD/.env           — project-level, UNTRUSTED: strict KEY=VALUE parse,
#                           values assigned literally, GUARD_* keys refused.
#
# The untrusted project file must never be executed and must never set a
# GUARD_*-namespaced variable, or a project-controlled .env could forge the
# per-process guard nonce (GUARD_ALLOW_PRIMARY_EDIT) or run arbitrary shell via
# BASH_ENV (ticket 0323, residual 2).
#
# Harness idiom: run bash-env.sh in an isolated subprocess with a controlled
# HOME (so the real ~/.claude/.env is never read) and a controlled project dir
# as PWD, then assert on the resulting environment.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/bash-env.sh"
fail=0

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Load bash-env.sh in a subprocess with $HOME=<home> and PWD=<projdir>, then
# print the value of environment variable <var> ("" if unset). stderr silenced.
_load_var() {
    local home="$1" projdir="$2" var="$3"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
        n="$3"
        printf "%s" "${!n-}"
    ' _ "$projdir" "$SCRIPT" "$var" 2>/dev/null
}

# Load bash-env.sh as above but return only the exit code (0 = no shell error).
_load_rc() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
    ' _ "$projdir" "$SCRIPT" >/dev/null 2>&1
    echo $?
}

_assert_eq() {
    local label="$1" got="$2" want="$3"
    if [[ "$got" == "$want" ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — got [$got], want [$want]"
        fail=1
    fi
}

_assert_file_absent() {
    local label="$1" path="$2"
    if [[ ! -e "$path" ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — file was created: $path"
        fail=1
    fi
}

# An empty HOME so no trusted ~/.claude/.env exists (isolates the project file).
EMPTY_HOME="$WORK/empty-home"
mkdir -p "$EMPTY_HOME"

# --- (1) a GUARD_* key in the project .env must NOT be set --------------------
P1="$WORK/p1"; mkdir -p "$P1"
printf 'GUARD_ALLOW_PRIMARY_EDIT=1\n' > "$P1/.env"
_assert_eq "project .env cannot set GUARD_ALLOW_PRIMARY_EDIT" \
    "$(_load_var "$EMPTY_HOME" "$P1" GUARD_ALLOW_PRIMARY_EDIT)" ""

# --- (1b) the LEADING-UNDERSCORE guard override pair must NOT be set -----------
# pretooluse-worktree-path-guard.sh reads _GUARD_WORKTREE_ROOT / _GUARD_PRIMARY_ROOT
# as an unconditional worktree-path override; a project .env forging both to equal
# values would bypass the deny guard. The GUARD_* refusal must also catch _GUARD_*.
P1B="$WORK/p1b"; mkdir -p "$P1B"
printf '_GUARD_WORKTREE_ROOT=/x\n_GUARD_PRIMARY_ROOT=/x\n' > "$P1B/.env"
_assert_eq "project .env cannot set _GUARD_WORKTREE_ROOT" \
    "$(_load_var "$EMPTY_HOME" "$P1B" _GUARD_WORKTREE_ROOT)" ""
_assert_eq "project .env cannot set _GUARD_PRIMARY_ROOT" \
    "$(_load_var "$EMPTY_HOME" "$P1B" _GUARD_PRIMARY_ROOT)" ""

# --- (2) a command substitution in the project .env must NOT execute ----------
P2="$WORK/p2"; mkdir -p "$P2"
PWNED="$WORK/pwned"
rm -f "$PWNED"
# If the file were sourced as code, $(touch ...) and `touch ...` would run and
# create $PWNED. Trigger the load FIRST, then check for the side effect.
{
    printf 'EVIL=$(touch %q)\n' "$PWNED"
    printf 'ALSO=`touch %q`\n' "$PWNED"
} > "$P2/.env"
rc2="$(_load_rc "$EMPTY_HOME" "$P2")"
_assert_file_absent "project .env command substitution does not execute" "$PWNED"
_assert_eq "project .env with command-substitution values loads without shell error" \
    "$rc2" "0"
# And the literal text is stored, not the command result.
_assert_eq "command-substitution value stored literally" \
    "$(_load_var "$EMPTY_HOME" "$P2" EVIL)" "\$(touch $PWNED)"

# --- (3) a plain KEY=VALUE loads exactly --------------------------------------
P3="$WORK/p3"; mkdir -p "$P3"
printf 'FOO=bar\n' > "$P3/.env"
_assert_eq "plain FOO=bar loads as bar" \
    "$(_load_var "$EMPTY_HOME" "$P3" FOO)" "bar"

# --- (4) a quoted value strips one quote pair, preserves the space ------------
P4="$WORK/p4"; mkdir -p "$P4"
printf 'BAZ="a b"\n' > "$P4/.env"
_assert_eq "quoted BAZ=\"a b\" loads as: a b" \
    "$(_load_var "$EMPTY_HOME" "$P4" BAZ)" "a b"

# --- (5) regression: trusted ~/.claude/.env still gets full source behavior ---
USER_HOME="$WORK/user-home"
mkdir -p "$USER_HOME/.claude"
printf 'USERKEY=uval\n' > "$USER_HOME/.claude/.env"
P5="$WORK/p5"; mkdir -p "$P5"   # project dir with NO .env — isolates the user file
_assert_eq "trusted ~/.claude/.env is sourced (USERKEY=uval)" \
    "$(_load_var "$USER_HOME" "$P5" USERKEY)" "uval"

exit "$fail"
