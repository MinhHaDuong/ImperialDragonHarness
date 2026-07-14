#!/usr/bin/env bash
# Robustness regressions for scripts/bash-env.sh (ticket 0335) — follow-ups from
# the #588 (strict-parse) and #593 (KEYS=) gaze reviews. Three nits:
#
#   1. CRLF tolerance — a Windows-edited project .env terminates lines with \r\n.
#      `read` strips only \n, so a trailing \r survives into every value and,
#      worse, into the last KEYS= provider name (corrupting the ^[a-z0-9-]+$
#      match). The strict parser must drop a trailing CR.
#   2. Size cap — bash-env.sh is sourced on EVERY bash subprocess. A pathological
#      or adversarial project .env must not tax each one: past a generous byte
#      cap the parse is skipped with a stderr warning, never partially parsed.
#   3. realpath set -e safety — the dedup `realpath "$HOME/.claude/.env"` fails
#      (exit 1) when the user file is absent; under an already-active `set -e` in
#      the sourcing shell that failed command substitution aborts bash-env.sh
#      mid-way. It must be guarded so the script always reaches its end.
#
# Harness idiom: run bash-env.sh in an isolated subprocess with a controlled
# HOME (so the real ~/.claude/.env is never read) and a controlled project dir
# as PWD, then assert on the resulting environment / exit code / stderr.
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

# Load bash-env.sh with `set -e` ALREADY ACTIVE in the sourcing shell, and print
# a sentinel that is only reached if the source did not abort mid-way. Prints
# "END" on success, "" if the source aborted. stderr silenced.
_load_sete_reaches_end() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        set -e
        cd "$1" || exit 1
        source "$2"
        printf "END"
    ' _ "$projdir" "$SCRIPT" 2>/dev/null || true
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

# Load bash-env.sh and capture only its stderr (for warning assertions).
_load_stderr() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
    ' _ "$projdir" "$SCRIPT" 2>&1 >/dev/null
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

_assert_contains() {
    local label="$1" hay="$2" needle="$3"
    if [[ "$hay" == *"$needle"* ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — [$needle] not found in stderr"
        fail=1
    fi
}

EMPTY_HOME="$WORK/empty-home"   # no ~/.claude/.env — isolates the project file
mkdir -p "$EMPTY_HOME"

# Fake HOME with a ~/.config/keys/ provider fixture — NON-secret sentinel only.
FHOME="$WORK/keys-home"
mkdir -p "$FHOME/.config/keys"
printf 'FAKE_HF=hfval\n' > "$FHOME/.config/keys/huggingface.env"

# --- (1) CRLF value: a trailing \r is stripped -------------------------------
# printf '\r\n' writes a CRLF line terminator (Windows-edited .env). `read`
# strips only the \n; the parser must drop the surviving \r so the value is clean.
P1="$WORK/p1"; mkdir -p "$P1"
printf 'FOO=bar\r\n' > "$P1/.env"
_assert_eq "(1) CRLF value FOO=bar loses its trailing CR" \
    "$(_load_var "$EMPTY_HOME" "$P1" FOO)" "bar"

# --- (2) CRLF on the KEYS= line: provider name is not \r-corrupted ------------
# A trailing \r on 'KEYS=huggingface' would make the provider name
# 'huggingface\r', failing ^[a-z0-9-]+$ and loading nothing. With CR stripped the
# provider resolves and its (sentinel) secret loads.
P2="$WORK/p2"; mkdir -p "$P2"
printf 'KEYS=huggingface\r\n' > "$P2/.env"
_assert_eq "(2) CRLF KEYS=huggingface resolves the provider (FAKE_HF=hfval)" \
    "$(_load_var "$FHOME" "$P2" FAKE_HF)" "hfval"

# --- (3) oversized project .env: parse is skipped, warned, shell survives -----
# Generate a file well past the 256 KiB cap. It must be skipped (FOO not loaded),
# a warning emitted to stderr, and the shell must not error or hang.
P3="$WORK/p3"; mkdir -p "$P3"
# Build ~600 KiB of filler by doubling a buffer — no pipe, so no SIGPIPE under
# this suite's `set -o pipefail` (the ticket-0332 trap).
_be_big="PADDING_LINE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"$'\n'
while [ "${#_be_big}" -lt 600000 ]; do _be_big="$_be_big$_be_big"; done
{ printf 'FOO=bar\n'; printf '%s' "$_be_big"; } > "$P3/.env"
unset _be_big
_assert_eq "(3) oversized project .env: parse skipped, FOO not loaded" \
    "$(_load_var "$EMPTY_HOME" "$P3" FOO)" ""
_assert_eq "(3) oversized project .env: shell survives (rc 0)" \
    "$(_load_rc "$EMPTY_HOME" "$P3")" "0"
_assert_contains "(3) oversized project .env: size-cap warning on stderr" \
    "$(_load_stderr "$EMPTY_HOME" "$P3")" "exceeds size cap"

# --- (4) realpath safety under an active set -e ------------------------------
# (4a) A project .env EXISTS but the user ~/.claude/.env is ABSENT: the dedup
# realpath on the missing user file fails, and under set -e must NOT abort.
P4="$WORK/p4"; mkdir -p "$P4"
printf 'AAA=bbb\n' > "$P4/.env"
_assert_eq "(4a) set -e + missing user .env: source reaches its end" \
    "$(_load_sete_reaches_end "$EMPTY_HOME" "$P4")" "END"
_assert_eq "(4a) set -e + missing user .env: project value still loads" \
    "$(_load_var "$EMPTY_HOME" "$P4" AAA)" "bbb"
# (4b) Neither file present: source must also reach its end under set -e.
P4B="$WORK/p4b"; mkdir -p "$P4B"   # no .env at all
_assert_eq "(4b) set -e + no .env at all: source reaches its end" \
    "$(_load_sete_reaches_end "$EMPTY_HOME" "$P4B")" "END"

exit "$fail"
