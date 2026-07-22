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

# Load bash-env.sh and print only its STDERR (diagnostic warnings).
_load_stderr() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
    ' _ "$projdir" "$SCRIPT" 2>&1 >/dev/null
}

# Load bash-env.sh and print `export -p` (the exported environment).
_load_exports() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
        export -p
    ' _ "$projdir" "$SCRIPT" 2>/dev/null
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

_assert_ne() {
    local label="$1" got="$2" notwant="$3"
    if [[ "$got" != "$notwant" ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — value is [$got], must NOT equal [$notwant]"
        fail=1
    fi
}

_assert_contains() {
    local label="$1" hay="$2" needle="$3"
    if [[ "$hay" == *"$needle"* ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — [$needle] not found"
        fail=1
    fi
}

_assert_not_contains() {
    local label="$1" hay="$2" needle="$3"
    if [[ "$hay" != *"$needle"* ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — [$needle] unexpectedly present"
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

# --- (6) strict-parse critical-name denylist (ticket 0345, policy a) -----------
# The untrusted project .env strict-parse loop must refuse shell/process/
# interpreter-critical export NAMES, not only GUARD_* keys. Attacker controls
# both name and value here, so an un-denied name is a direct injection into
# every subprocess: GCONV_PATH → glibc iconv-module RCE, PATH → interpreter
# clobber, LD_PRELOAD/BASH_ENV → code execution, PYTHONPATH/NODE_OPTIONS →
# interpreter hijack. The shared predicate _be_is_protected_name refuses them
# on the strict-parse path (mirroring the KEYS-selection path).

# (6a) GCONV_PATH is refused (not exported) with a warning.
P6="$WORK/p6"; mkdir -p "$P6"
printf 'GCONV_PATH=/evil\n' > "$P6/.env"
_assert_eq "project .env cannot set GCONV_PATH" \
    "$(_load_var "$EMPTY_HOME" "$P6" GCONV_PATH)" ""
_assert_contains "project .env GCONV_PATH warns 'refusing protected name'" \
    "$(_load_stderr "$EMPTY_HOME" "$P6")" "refusing protected name from project .env: GCONV_PATH"

# (6b) PATH is not overwritten by a project .env; the real inherited PATH stays.
P6B="$WORK/p6b"; mkdir -p "$P6B"
printf 'PATH=/evil\n' > "$P6B/.env"
_assert_ne "project .env cannot overwrite PATH with /evil" \
    "$(_load_var "$EMPTY_HOME" "$P6B" PATH)" "/evil"
_assert_contains "project .env PATH warns 'refusing protected name'" \
    "$(_load_stderr "$EMPTY_HOME" "$P6B")" "refusing protected name from project .env: PATH"

# (6c) parametrized: each critical name is refused (value never equals its
# payload) and warns. IFS is checked additionally via the export attribute
# (its value is restored to the caller's, not a clean discriminator alone).
_be0345_case() {  # <key> <payload>
    local key="$1" payload="$2" dir="$WORK/p6c_$1"
    mkdir -p "$dir"
    printf '%s=%s\n' "$key" "$payload" > "$dir/.env"
    _assert_ne "project .env cannot set $key" \
        "$(_load_var "$EMPTY_HOME" "$dir" "$key")" "$payload"
    _assert_contains "project .env $key warns 'refusing protected name'" \
        "$(_load_stderr "$EMPTY_HOME" "$dir")" "refusing protected name from project .env: $key"
}
_be0345_case PYTHONPATH /evil
_be0345_case NODE_OPTIONS --require=/evil
_be0345_case NODE_PATH /evil
_be0345_case PERL5LIB /evil
_be0345_case RUBYOPT -r/evil
_be0345_case LD_PRELOAD /evil.so
_be0345_case LD_LIBRARY_PATH /evil
_be0345_case LD_AUDIT /evil.so
_be0345_case BASH_ENV /evil
_be0345_case ENV /evil
_be0345_case IFS x
# git command-execution vectors: the harness runs git constantly, so a project
# .env setting one is a direct RCE (GIT_SSH_COMMAND runs on every fetch/push,
# GIT_ASKPASS/GIT_EXTERNAL_DIFF on their respective operations).
_be0345_case GIT_SSH_COMMAND 'ssh -oProxyCommand=evil'
_be0345_case GIT_SSH /evil
_be0345_case GIT_ASKPASS /evil
_be0345_case GIT_EXTERNAL_DIFF /evil
# pager input/close hooks: a `|cmd %s` LESSOPEN runs on every `git log` / `less`.
_be0345_case LESSOPEN '|evil %s'
_be0345_case LESSCLOSE '|evil %s'
# lower-severity perturbation vars (ticket 0352): not code-execution vectors, but
# a hostile project .env should not be able to steer a child's timezone, terminal
# database, prompt-0, dynamic-linker diagnostics, xtrace fd, or history file.
_be0345_case PS0 /evil
_be0345_case LD_DEBUG all
_be0345_case LD_PROFILE /evil.so
_be0345_case TZ /evil
_be0345_case TZDIR /evil
_be0345_case LOCALDOMAIN evil
_be0345_case TERMINFO /evil
_be0345_case BASH_XTRACEFD 2
_be0345_case HISTFILE /evil

# (6d) IFS must not be turned into an exported variable by a project .env.
P6D="$WORK/p6d"; mkdir -p "$P6D"
printf 'IFS=x\n' > "$P6D/.env"
_assert_not_contains "project .env IFS is NOT exported" \
    "$(_load_exports "$EMPTY_HOME" "$P6D")" "declare -x IFS"

# (6e) the _be_* bookkeeping namespace is also refused (would corrupt the loop).
P6E="$WORK/p6e"; mkdir -p "$P6E"
printf '_be_key=hijack\n' > "$P6E/.env"
_assert_eq "project .env cannot set _be_ bookkeeping var" \
    "$(_load_var "$EMPTY_HOME" "$P6E" _be_key)" ""

# --- (7) regression: benign non-critical keys still load normally -------------
P7="$WORK/p7"; mkdir -p "$P7"
printf 'PROJECT_DATA=/some/path\n' > "$P7/.env"
_assert_eq "benign PROJECT_DATA still exports" \
    "$(_load_var "$EMPTY_HOME" "$P7" PROJECT_DATA)" "/some/path"

# (7b) a KEYS= line is not a protected name; it still parses as a plain value.
P7B="$WORK/p7b"; mkdir -p "$P7B"
printf 'KEYS=someprovider\n' > "$P7B/.env"
_assert_eq "KEYS= line still parses (not refused as protected)" \
    "$(_load_var "$EMPTY_HOME" "$P7B" KEYS)" "someprovider"

exit "$fail"
