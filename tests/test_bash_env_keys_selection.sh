#!/usr/bin/env bash
# Tests for the KEYS= least-privilege provider-secret loading in scripts/bash-env.sh.
#
# A project opts into provider secrets by declaring KEYS=prov1,prov2 in its project
# $PWD/.env. bash-env.sh then sources ONLY $HOME/.config/keys/<prov>.env for each
# declared, VALIDATED provider. Default-deny: no KEYS line -> no provider secrets
# loaded. Provider names are validated against ^[a-z0-9-]+$ so a crafted KEYS value
# cannot escape ~/.config/keys/ via path traversal (../../etc/passwd, foo/bar, ...).
#
# The ~/.config/keys/<name>.env files are user-owned and TRUSTED, so they are sourced
# as shell code (contrast the untrusted project .env, which is strict-parsed). This
# suite never touches the real ~/.config/keys — it builds a FAKE HOME temp dir whose
# fixtures hold NON-secret sentinel values only.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/bash-env.sh"
fail=0

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Fake HOME with ~/.config/keys/ provider fixtures — NON-secret sentinels only.
FHOME="$WORK/home"
mkdir -p "$FHOME/.config/keys"
printf 'FAKE_OPENROUTER=orval\n' > "$FHOME/.config/keys/openrouter.env"
printf 'FAKE_MISTRAL=mval\n'     > "$FHOME/.config/keys/mistral.env"
printf 'FAKE_ZENODO=zval\n'      > "$FHOME/.config/keys/zenodo.env"

# Load bash-env.sh in a subprocess with $HOME=<home> and PWD=<projdir>, then print
# the value of environment variable <var> ("" if unset). stderr silenced.
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

# Load bash-env.sh as above and print `export -p` (the exported environment) so a
# caller can assert whether a variable is or is not marked for export.
_load_exports() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
        export -p
    ' _ "$projdir" "$SCRIPT" 2>/dev/null
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

_assert_eq() {
    local label="$1" got="$2" want="$3"
    if [[ "$got" == "$want" ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — got [$got], want [$want]"
        fail=1
    fi
}

# Make a project dir <name> holding <env-content> as its .env; echo the dir path.
_mkproj() {
    local dir="$WORK/$1"
    mkdir -p "$dir"
    printf '%s' "$2" > "$dir/.env"
    printf '%s' "$dir"
}

# --- (1) only the declared provider loads; undeclared providers do NOT -----------
P1="$(_mkproj p1 'KEYS=openrouter
')"
_assert_eq "(1) declared openrouter loads (FAKE_OPENROUTER=orval)" \
    "$(_load_var "$FHOME" "$P1" FAKE_OPENROUTER)" "orval"
_assert_eq "(1) undeclared mistral is NOT loaded" \
    "$(_load_var "$FHOME" "$P1" FAKE_MISTRAL)" ""

# --- (2) no KEYS line at all -> default-deny, nothing loaded ---------------------
P2="$(_mkproj p2 'FOO=bar
')"
_assert_eq "(2) default-deny: openrouter not loaded" \
    "$(_load_var "$FHOME" "$P2" FAKE_OPENROUTER)" ""
_assert_eq "(2) default-deny: mistral not loaded" \
    "$(_load_var "$FHOME" "$P2" FAKE_MISTRAL)" ""

# --- (3) multiple declared providers all load -----------------------------------
P3="$(_mkproj p3 'KEYS=openrouter,zenodo
')"
_assert_eq "(3) multi: openrouter loads" \
    "$(_load_var "$FHOME" "$P3" FAKE_OPENROUTER)" "orval"
_assert_eq "(3) multi: zenodo loads" \
    "$(_load_var "$FHOME" "$P3" FAKE_ZENODO)" "zval"
_assert_eq "(3) multi: undeclared mistral not loaded" \
    "$(_load_var "$FHOME" "$P3" FAKE_MISTRAL)" ""

# --- (3b) whitespace around names is trimmed ------------------------------------
P3B="$(_mkproj p3b 'KEYS= openrouter , zenodo
')"
_assert_eq "(3b) spaced: openrouter loads" \
    "$(_load_var "$FHOME" "$P3B" FAKE_OPENROUTER)" "orval"
_assert_eq "(3b) spaced: zenodo loads" \
    "$(_load_var "$FHOME" "$P3B" FAKE_ZENODO)" "zval"

# --- (4) path-traversal / invalid names are rejected: nothing sourced, no error --
P4="$(_mkproj p4 'KEYS=../../etc/passwd
')"
_assert_eq "(4a) traversal name: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P4")" "0"
_assert_eq "(4a) traversal name: nothing spurious loaded" \
    "$(_load_var "$FHOME" "$P4" FAKE_OPENROUTER)" ""
P4B="$(_mkproj p4b 'KEYS=foo/bar
')"
_assert_eq "(4b) slash name: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P4B")" "0"
_assert_eq "(4b) slash name: nothing loaded" \
    "$(_load_var "$FHOME" "$P4B" FAKE_OPENROUTER)" ""

# --- (5) declared-but-nonexistent provider -> warns, no error, nothing spurious --
P5="$(_mkproj p5 'KEYS=nonexistent
')"
_assert_eq "(5) nonexistent provider: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P5")" "0"
_assert_eq "(5) nonexistent provider: nothing loaded" \
    "$(_load_var "$FHOME" "$P5" FAKE_OPENROUTER)" ""

# --- (6) export hygiene: provider vars export; IFS and _be_* temporaries do NOT --
# Enabling allexport only around each `source` must export exactly what the
# provider file assigns. IFS and the loop-bookkeeping temporaries are assigned
# outside allexport, so they must never leak into the child environment.
P6="$(_mkproj p6 'KEYS=openrouter
')"
P6_EXPORTS="$(_load_exports "$FHOME" "$P6")"
_assert_contains "(6) provider var IS exported (FAKE_OPENROUTER)" \
    "$P6_EXPORTS" "FAKE_OPENROUTER"
_assert_not_contains "(6) IFS is NOT exported" \
    "$P6_EXPORTS" "declare -x IFS"
_assert_not_contains "(6) no _be_ temporary is exported" \
    "$P6_EXPORTS" "declare -x _be_"

# --- (7) glob-safety: KEYS=* stays literal, is rejected, sources nothing ---------
# A decoy file next to the project must not tempt the '*' to expand: set -f keeps
# it literal, validation rejects it, and nothing is sourced.
P7="$(_mkproj p7 'KEYS=*
')"
touch "$P7/decoy.env"
_assert_eq "(7) glob KEYS=*: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P7")" "0"
_assert_eq "(7) glob KEYS=*: nothing sourced" \
    "$(_load_var "$FHOME" "$P7" FAKE_OPENROUTER)" ""

# --- (8) uppercase provider names are rejected by ^[a-z0-9-]+$ -------------------
P8="$(_mkproj p8 'KEYS=OpenRouter
')"
_assert_eq "(8) uppercase name: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P8")" "0"
_assert_eq "(8) uppercase name: nothing loaded" \
    "$(_load_var "$FHOME" "$P8" FAKE_OPENROUTER)" ""

exit "$fail"
