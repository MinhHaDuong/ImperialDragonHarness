#!/usr/bin/env bash
# Tests for skills/update-publist/resolve_hal_credentials.sh (ticket 0944).
#
# The script resolves ONE named HAL credential variable out of the keystore
# file at point of use, so the HAL deposit stops depending on the ambient
# environment (and on the cwd-dependent `KEYS=` selection, ticket 0360).
#
# NO REAL CREDENTIAL IS USED OR NEEDED ANYWHERE IN THIS SUITE. Every fixture
# value is an obviously-fake sentinel in a fake keystore under a fake HOME; the
# real `~/.config/keys/hal.env` is never read, because every child is spawned
# with `env -i` and an explicit `HAL_KEYSTORE_FILE` (or an explicit fake HOME).
#
# Hygiene this suite holds itself to, mirroring the one it tests: a resolved
# value never reaches this shell's stdout, a failure message, or an argv. The
# children compare in-process and report BOOLEANS and MARKER NAMES only. A
# failing assertion here must not become the leak it is testing for
# (rules/coding-bash.md; the 2026-07-27 incident).
#
# WHY `env -i` ON EVERY SPAWN. BASH_ENV points every child bash at
# scripts/bash-env.sh, which re-runs credential selection at child startup — so
# a plain `bash -c` would hand the child the LIVE HAL credential, masking the
# fixture and printing a real secret on failure. `env -i` is the remedy
# tests/test_bash_tests_are_hermetic.sh enforces, and this suite uses it
# uniformly rather than the suite-wide `export BASH_ENV=` exemption.
#
# TWO DIFFERENT ISOLATION LAYERS, DO NOT CONFLATE THEM:
#   * the `env -i` on the spawns BELOW isolates the TEST from the live harness;
#   * the `env -i` INSIDE the resolver isolates the keystore extraction from
#     the caller. Case (2)/(3) is what actually tests the second one, and it
#     is invisible to case (1).
#
# WHY THE GRANDCHILD PROBE IS `env`, NOT `bash -c`. Case (2)/(3) must observe
# what a child of the CALLING shell inherits, so that grandchild must NOT be
# hermetic — it has to inherit. `env` is exactly that observation (the
# environment a freshly spawned process receives) and keeps every `bash` spawn
# in this file textually hermetic, so the 0359 guard reads this suite as it
# really is instead of being talked around with a heredoc-written script. The
# companion `own:` markers cover the complementary case an `env` probe cannot
# see on its own: a leak into a NON-exported shell variable of the caller.
set -euo pipefail

cd "$(dirname "$0")/.."
RESOLVER="$PWD/skills/update-publist/resolve_hal_credentials.sh"
fail=0

ok()   { echo "PASS: $1"; }
bad()  { echo "FAIL: $1" >&2; fail=1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- fixtures: fake HOME, fake keystore, obviously-fake sentinels ------------
FHOME="$WORK/home"
mkdir -p "$FHOME/.config/keys"
KEYFILE="$FHOME/.config/keys/hal.env"

ID_SENTINEL='fake-hal-id-sentinel-0944'
PW_SENTINEL='fake-hal-password-sentinel-0944'
DECOY_SENTINEL='should-never-appear'

# The DECOY is the whole point of the fixture. A named extraction and a
# wholesale `. hal.env` produce IDENTICAL output on the happy path; only a
# third variable that the caller never asked for tells them apart.
printf 'HAL_ID=%s\nHAL_PASSWORD=%s\nHAL_DECOY=%s\n' \
    "$ID_SENTINEL" "$PW_SENTINEL" "$DECOY_SENTINEL" > "$KEYFILE"

# A keystore missing HAL_PASSWORD, for the loud-failure case.
PARTIAL="$WORK/partial.env"
printf 'HAL_ID=%s\nHAL_DECOY=%s\n' "$ID_SENTINEL" "$DECOY_SENTINEL" > "$PARTIAL"

# A keystore whose HAL_ID is defined but empty: a silent-empty success would
# build a half-empty curl config and surface as an HAL auth error.
EMPTYVAL="$WORK/emptyval.env"
printf 'HAL_ID=\n' > "$EMPTYVAL"

# --- (0) the script exists and is executable ---------------------------------
if [ -x "$RESOLVER" ]; then
    ok "(0) resolver exists and is executable"
else
    bad "(0) resolver is missing or not executable: skills/update-publist/resolve_hal_credentials.sh"
    echo "--- $(basename "$0"): $fail failing case(s) ---" >&2
    exit 1
fi

# --- (1) happy path: each variable resolves to ITS OWN value ------------------
# Catches a wrong value, the wrong variable, the wrong file, and a silent-empty
# success. The comparison happens inside the child; only MATCH/MISMATCH is
# printed, never the value.
_match_via_keystore_file() {  # $1 variable name, $2 expected sentinel
    env -i HOME="$FHOME" PATH="$PATH" HAL_KEYSTORE_FILE="$KEYFILE" bash -c '
        v="$("$1" "$2")" || { printf "EXIT_%s" "$?"; exit 0; }
        if [ "$v" = "$3" ]; then printf "MATCH"; else printf "MISMATCH"; fi
    ' _ "$RESOLVER" "$1" "$2" 2>/dev/null
}

for probe in "HAL_ID:$ID_SENTINEL" "HAL_PASSWORD:$PW_SENTINEL"; do
    got="$(_match_via_keystore_file "${probe%%:*}" "${probe#*:}")"
    if [ "$got" = "MATCH" ]; then
        ok "(1) ${probe%%:*} resolves to its own value"
    else
        bad "(1) ${probe%%:*} did not resolve to its own value (probe said: $got)"
    fi
done

# --- (1b) the default provider path is ~/.config/keys/hal.env ----------------
# Without the test-only HAL_KEYSTORE_FILE override, the resolver must find the
# file under HOME by itself — otherwise every case above would be testing the
# override rather than the shipped default.
got="$(env -i HOME="$FHOME" PATH="$PATH" bash -c '
    v="$("$1" HAL_ID)" || { printf "EXIT_%s" "$?"; exit 0; }
    if [ "$v" = "$2" ]; then printf "MATCH"; else printf "MISMATCH"; fi
' _ "$RESOLVER" "$ID_SENTINEL" 2>/dev/null)"
if [ "$got" = "MATCH" ]; then
    ok "(1b) default provider path under HOME resolves"
else
    bad "(1b) default provider path under HOME did not resolve (probe said: $got)"
fi

# --- (2) leak probe + (3) decoy ----------------------------------------------
# The calling shell invokes the resolver the way SKILL.md documents it —
# COMMAND SUBSTITUTION, not `source` — then asks what it and its children can
# see. A correct implementation resolves the value into one shell variable of
# the caller's choosing and implants nothing: no HAL_* variable of its own in
# the caller, and none in the caller's children.
#
# `out` accumulates MARKER NAMES only (`own:NAME` / `child:NAME`), never values.
leak="$(env -i HOME="$FHOME" PATH="$PATH" HAL_KEYSTORE_FILE="$KEYFILE" bash -c '
    resolver="$1"; expected="$2"
    hal_id_value="$("$resolver" HAL_ID)" || { printf "EXIT_%s" "$?"; exit 0; }
    [ "$hal_id_value" = "$expected" ] || { printf "RESOLVE_FAILED"; exit 0; }
    out=""
    for n in HAL_ID HAL_PASSWORD HAL_DECOY; do
        [ -n "${!n+x}" ] && out="$out own:$n"
        env | grep -q "^${n}=" && out="$out child:$n"
    done
    printf "%s" "${out:-CLEAN}"
' _ "$RESOLVER" "$ID_SENTINEL" 2>/dev/null)"

case "$leak" in
    CLEAN|*"own:"*|*"child:"*) ;;
    *) bad "(2/3) the leak probe did not run to completion (probe said: $leak)" ;;
esac

if [ "$leak" = "CLEAN" ] || [ "${leak//HAL_DECOY/}" = "$leak" ]; then
    ok "(3) the decoy variable is invisible to the caller and its children"
else
    bad "(3) the decoy variable leaked — a wholesale source, not a named extraction ($leak)"
fi

case "$leak" in
    *HAL_ID*|*HAL_PASSWORD*)
        bad "(2) a resolved credential variable leaked into the caller or its children ($leak)" ;;
    *)
        ok "(2) no resolved credential variable reaches the caller or its children" ;;
esac

# --- (4) loud, named failures -------------------------------------------------
# Each case asserts the exit code AND that the message names the variable and
# the file, then asserts that NO sentinel value appears in that message.
_stderr_of() {  # $1 keystore file (may not exist), $2 variable name; prints stderr
    env -i HOME="$FHOME" PATH="$PATH" HAL_KEYSTORE_FILE="$1" bash -c \
        '"$1" "$2"' _ "$RESOLVER" "$2" 2>&1 >/dev/null || true
}
_rc_of() {  # same args; prints the exit code
    local rc=0
    env -i HOME="$FHOME" PATH="$PATH" HAL_KEYSTORE_FILE="$1" bash -c \
        '"$1" "$2"' _ "$RESOLVER" "$2" >/dev/null 2>&1 || rc=$?
    printf '%s' "$rc"
}

MISSING="$WORK/absent.env"

rc="$(_rc_of "$MISSING" HAL_ID)"
err="$(_stderr_of "$MISSING" HAL_ID)"
if [ "$rc" = 2 ] && [[ "$err" == *"$MISSING"* && "$err" == *HAL_ID* ]]; then
    ok "(4a) unreadable keystore exits 2 and names the file and the variable"
else
    bad "(4a) unreadable keystore: expected exit 2 naming the file and the variable, got exit $rc"
fi

rc="$(_rc_of "$PARTIAL" HAL_PASSWORD)"
err="$(_stderr_of "$PARTIAL" HAL_PASSWORD)"
if [ "$rc" = 4 ] && [[ "$err" == *"$PARTIAL"* && "$err" == *HAL_PASSWORD* ]]; then
    ok "(4b) absent variable exits 4 and names the variable and the file"
else
    bad "(4b) absent variable: expected exit 4 naming the variable and the file, got exit $rc"
fi
if [[ "$err" == *"$ID_SENTINEL"* || "$err" == *"$DECOY_SENTINEL"* ]]; then
    bad "(4b) the failure message disclosed a value from the keystore"
else
    ok "(4b) the failure message discloses no value from the keystore"
fi

rc="$(_rc_of "$EMPTYVAL" HAL_ID)"
if [ "$rc" = 4 ]; then
    ok "(4c) a defined-but-empty credential fails loud (exit 4) instead of succeeding silently"
else
    bad "(4c) a defined-but-empty credential returned exit $rc, expected 4"
fi

# An invalid variable name is rejected before it can reach the extraction — and
# the rejected string is not echoed back, since an operator who mistypes the
# call may well have pasted a VALUE where a NAME belongs.
rc="$(_rc_of "$KEYFILE" 'HAL_ID; echo pwned')"
err="$(_stderr_of "$KEYFILE" 'HAL_ID; echo pwned')"
if [ "$rc" = 1 ] && [[ "$err" != *pwned* ]]; then
    ok "(4d) an invalid variable name exits 1 without echoing the rejected string"
else
    bad "(4d) invalid variable name: expected exit 1 and no echo of the argument, got exit $rc"
fi

echo "--- $(basename "$0"): $fail failing case(s) ---"
exit "$fail"
