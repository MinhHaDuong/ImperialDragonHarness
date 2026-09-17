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
# with `env -i` and is handed an explicit fixture path (or an explicit fake
# HOME, for the default-path case).
#
# Hygiene this suite holds itself to, mirroring the one it tests: a resolved
# value never reaches this shell's stdout, a failure message, or an argv. The
# children compare in-process and report BOOLEANS and MARKER NAMES only. A
# failing assertion here must not become the leak it is testing for
# (rules/coding-bash.md; the 2026-07-27 incident).
#
# WHY `env -i` ON EVERY SPAWN. BASH_ENV points every child bash at
# scripts/bash-env.sh, and a plain `bash -c` also inherits any ambient HAL
# credential. Either can mask the fixture and print a real secret on failure.
# `env -i` is the remedy
# tests/test_bash_tests_are_hermetic.sh enforces, and this suite uses it
# uniformly rather than the suite-wide `export BASH_ENV=` exemption.
#
# TWO DIFFERENT ISOLATION LAYERS, AND WHICH CASE TESTS WHICH. The `env -i` on
# the spawns below isolates the TEST from the live harness. The `env -i` INSIDE
# the resolver isolates the keystore extraction from its caller. They are not
# the same property and no single case covers both:
#
#   * (1)/(1b) test the value, the variable and the file, and nothing else.
#   * (2)/(3) test the CALLER-SIDE property: invoking the resolver the way
#     SKILL.md documents it implants nothing in the caller or its children.
#     What they discriminate is the shape the ticket rejected — a caller that
#     does `set -a; . ~/.config/keys/hal.env` itself, which leaks all three
#     variables including the decoy. What they do NOT discriminate, and cannot,
#     is a resolver that sources wholesale INSIDE its own process: that is a
#     separate process, so there is nowhere for it to leak to. An earlier
#     revision of this file claimed otherwise; review of PR #941 disproved it
#     by building that resolver and watching these cases stay green.
#   * (2b)/(2c) are what pin the resolver's OWN `env -i`. (2b) is behavioural —
#     an ambient value must never satisfy a lookup, and must never win over the
#     file. (2c) is direct: the fixture dumps the environment of the very
#     subshell that sources it, and a marker exported by the caller must not be
#     in that dump. Delete `env -i` from the resolver and both go red.
#
# WHY THE GRANDCHILD PROBE IN (2)/(3) IS `env`, NOT `bash -c`. It must observe
# what a child of the CALLING shell inherits, so that grandchild must NOT be
# hermetic — inheriting is the whole observation. `env` is exactly that
# observation, and it keeps every `bash` spawn in this file textually hermetic,
# so the 0359 guard reads this suite as it really is instead of being talked
# around with a heredoc-written script. The companion `own:` markers cover the
# complementary case an `env` probe cannot see: a leak into a NON-exported
# shell variable of the caller.
set -euo pipefail

cd "$(dirname "$0")/.."
RESOLVER="$PWD/skills/update-publist/resolve_hal_credentials.sh"
fail=0

ok()   { echo "PASS: $1"; }
bad()  { echo "FAIL: $1" >&2; fail=$((fail + 1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- fixtures: fake HOME, fake keystore, obviously-fake sentinels ------------
FHOME="$WORK/home"
mkdir -p "$FHOME/.config/keys"
KEYFILE="$FHOME/.config/keys/hal.env"

ID_SENTINEL='fake-hal-id-sentinel-0944'
PW_SENTINEL='fake-hal-password-sentinel-0944'
DECOY_SENTINEL='should-never-appear'
AMBIENT_SENTINEL='fake-ambient-value-that-must-never-win'

# The DECOY is the whole point of the fixture. A named extraction and a
# wholesale `. hal.env` produce IDENTICAL output on the happy path; only a
# third variable that the caller never asked for tells them apart.
printf 'HAL_ID=%s\nHAL_PASSWORD=%s\nHAL_DECOY=%s\n' \
    "$ID_SENTINEL" "$PW_SENTINEL" "$DECOY_SENTINEL" > "$KEYFILE"

# A keystore missing HAL_PASSWORD, for the loud-failure and ambient cases.
PARTIAL="$WORK/partial.env"
printf 'HAL_ID=%s\nHAL_DECOY=%s\n' "$ID_SENTINEL" "$DECOY_SENTINEL" > "$PARTIAL"

# A keystore whose HAL_ID is defined but empty: a silent-empty success would
# build a half-empty curl config and surface as an HAL auth error.
EMPTYVAL="$WORK/emptyval.env"
printf 'HAL_ID=\n' > "$EMPTYVAL"

# A keystore that cannot be parsed as shell at all.
UNPARSABLE="$WORK/unparsable.env"
printf 'HAL_ID=(((\n' > "$UNPARSABLE"

# A keystore that exits before defining anything. Its subshell ends with status
# 0 and no output, which without a completion marker is indistinguishable from
# a successfully extracted empty string.
EARLYEXIT="$WORK/earlyexit.env"
printf 'exit 0\nHAL_ID=%s\n' "$ID_SENTINEL" > "$EARLYEXIT"

# A CRLF keystore. Without a CR strip the value carries a trailing carriage
# return into the curl config and the deposit fails as an HAL auth error.
CRLF="$WORK/crlf.env"
printf 'HAL_ID=%s\r\nHAL_PASSWORD=%s\r\n' "$ID_SENTINEL" "$PW_SENTINEL" > "$CRLF"

# A keystore whose value spans two lines. `curl -K` parses one directive per
# line, so this must be refused at resolution — the caller's quoting layer sits
# above the line boundary and cannot reach it.
MULTILINE="$WORK/multiline.env"
printf "HAL_PASSWORD='first-line\nsecond-line'\n" > "$MULTILINE"
TRAILING_LF="$WORK/trailing-lf.env"
printf "HAL_PASSWORD='line-with-trailing-lf\n'\n" > "$TRAILING_LF"

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
_match_in_file() {  # $1 keystore file, $2 variable name, $3 expected sentinel
    env -i HOME="$FHOME" PATH="$PATH" bash -c '
        v="$("$1" "$3" "$2")" || { printf "EXIT_%s" "$?"; exit 0; }
        if [ "$v" = "$4" ]; then printf "MATCH"; else printf "MISMATCH"; fi
    ' _ "$RESOLVER" "$1" "$2" "$3" 2>/dev/null
}

for probe in "HAL_ID:$ID_SENTINEL" "HAL_PASSWORD:$PW_SENTINEL"; do
    got="$(_match_in_file "$KEYFILE" "${probe%%:*}" "${probe#*:}")"
    if [ "$got" = "MATCH" ]; then
        ok "(1) ${probe%%:*} resolves to its own value"
    else
        bad "(1) ${probe%%:*} did not resolve to its own value (probe said: $got)"
    fi
done

# --- (1b) the default provider path is ~/.config/keys/hal.env ----------------
# Called with ONE argument, the resolver must find the file under HOME by
# itself — otherwise every case above would be testing the test-only path
# argument rather than the shipped default.
got="$(env -i HOME="$FHOME" PATH="$PATH" bash -c '
    v="$("$1" HAL_ID)" || { printf "EXIT_%s" "$?"; exit 0; }
    if [ "$v" = "$2" ]; then printf "MATCH"; else printf "MISMATCH"; fi
' _ "$RESOLVER" "$ID_SENTINEL" 2>/dev/null)"
if [ "$got" = "MATCH" ]; then
    ok "(1b) the one-argument form resolves the default path under HOME"
else
    bad "(1b) the one-argument form did not resolve the default path under HOME (probe said: $got)"
fi

# --- (2) caller-side leak probe + (3) decoy ----------------------------------
# The calling shell invokes the resolver the way SKILL.md documents it —
# COMMAND SUBSTITUTION, not `source` — then asks what it and its children can
# see. Scope of the claim: see the header. This discriminates the rejected
# caller-side `. hal.env`, not a resolver's internals.
#
# `out` accumulates MARKER NAMES only (`own:NAME` / `child:NAME`), never values.
_leak_markers() {  # $1 shell snippet that is expected to obtain HAL_ID
    env -i HOME="$FHOME" PATH="$PATH" KEYFILE="$KEYFILE" RESOLVER="$RESOLVER" bash -c '
        eval "$1"
        out=""
        for n in HAL_ID HAL_PASSWORD HAL_DECOY; do
            [ -n "${!n+x}" ] && out="$out own:$n"
            env | grep -q "^${n}=" && out="$out child:$n"
        done
        printf "%s" "${out:-CLEAN}"
    ' _ "$1" 2>/dev/null
}

# (2/3-control) The REJECTED shape, run first: a caller that sources the
# provider file wholesale. If this comes back CLEAN the probe is blind and the
# green below would prove nothing — the positive control fires before the
# measurement, not after it.
control="$(_leak_markers 'set -a; . "$KEYFILE"; set +a')"
case "$control" in
    *child:HAL_DECOY*)
        ok "(2/3-control) the probe does detect the rejected wholesale source" ;;
    *)
        bad "(2/3-control) the probe is blind: the rejected wholesale source came back '$control'" ;;
esac

leak="$(_leak_markers 'hal_id_value="$("$RESOLVER" HAL_ID "$KEYFILE")"')"

case "$leak" in
    CLEAN|*"own:"*|*"child:"*) ;;
    *) bad "(2/3) the leak probe did not run to completion (probe said: $leak)" ;;
esac

if [ "${leak//HAL_DECOY/}" = "$leak" ]; then
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

# --- (2b) the ambient environment is not consulted ----------------------------
# The documented contract is that a pre-set HAL_ID / HAL_PASSWORD has no effect
# at all. Two directions, and the second is the discriminating one: a resolver
# that dropped its internal `env -i` would resolve the AMBIENT value for a name
# the file does not define, and a resolver copying the reviewers.sh
# prefer-the-environment branch would return the ambient value even when the
# file does define it.
got="$(env -i HOME="$FHOME" PATH="$PATH" HAL_ID="$AMBIENT_SENTINEL" bash -c '
    v="$("$1" HAL_ID "$2")" || { printf "EXIT_%s" "$?"; exit 0; }
    if [ "$v" = "$3" ]; then printf "FILE_WINS"
    elif [ "$v" = "$4" ]; then printf "AMBIENT_WINS"
    else printf "NEITHER"; fi
' _ "$RESOLVER" "$KEYFILE" "$ID_SENTINEL" "$AMBIENT_SENTINEL" 2>/dev/null)"
if [ "$got" = "FILE_WINS" ]; then
    ok "(2b) the keystore value wins over an ambient value of the same name"
else
    bad "(2b) an ambient value influenced the result (probe said: $got)"
fi

got="$(env -i HOME="$FHOME" PATH="$PATH" HAL_PASSWORD="$AMBIENT_SENTINEL" bash -c '
    v="$("$1" HAL_PASSWORD "$2")" || { printf "EXIT_%s" "$?"; exit 0; }
    if [ "$v" = "$3" ]; then printf "AMBIENT_WINS"; else printf "SOMETHING_ELSE"; fi
' _ "$RESOLVER" "$PARTIAL" "$AMBIENT_SENTINEL" 2>/dev/null)"
if [ "$got" = "EXIT_4" ]; then
    ok "(2b) an ambient value cannot stand in for a variable the keystore lacks"
else
    bad "(2b) a variable absent from the keystore did not fail loud (probe said: $got)"
fi

# --- (2c) the extraction subshell really runs under a cleared environment -----
# Direct observation rather than inference: the fixture dumps the environment
# of the very subshell that sources it, and the caller exports a marker that
# must not appear there. This is the case that goes red if `env -i` is dropped
# from the resolver.
if [ -x /usr/bin/env ]; then
    DUMP="$WORK/introspect.dump"
    INTROSPECT="$WORK/introspect.env"
    { printf 'HAL_ID=%s\n' "$ID_SENTINEL"
      printf "/usr/bin/env > '%s'\n" "$DUMP"; } > "$INTROSPECT"
    env -i HOME="$FHOME" PATH="$PATH" HAL_AMBIENT_MARKER="$AMBIENT_SENTINEL" bash -c \
        '"$1" HAL_ID "$2" >/dev/null' _ "$RESOLVER" "$INTROSPECT" 2>/dev/null || true
    if [ ! -s "$DUMP" ]; then
        bad "(2c) the introspection fixture produced no dump — the probe did not run"
    elif grep -q '^HAL_AMBIENT_MARKER=' "$DUMP"; then
        bad "(2c) the extraction subshell inherited the caller's environment — env -i is not in force"
    else
        ok "(2c) the extraction subshell inherits nothing from the caller"
    fi
else
    bad "(2c) /usr/bin/env is missing — this probe cannot run, so its silence means nothing"
fi

# --- (4) loud, named failures -------------------------------------------------
# Each case asserts the exit code AND that the message names the variable and
# the file, then asserts that NO sentinel value appears in that message.
_stderr_of() {  # $1 keystore file (may not exist), $2 variable name
    env -i HOME="$FHOME" PATH="$PATH" bash -c \
        '"$1" "$3" "$2"' _ "$RESOLVER" "$1" "$2" 2>&1 >/dev/null || true
}
_rc_of() {  # same args; prints the exit code
    local rc=0
    env -i HOME="$FHOME" PATH="$PATH" bash -c \
        '"$1" "$3" "$2"' _ "$RESOLVER" "$1" "$2" >/dev/null 2>&1 || rc=$?
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

# The name argument is an ALLOWLIST of the two credentials the deposit needs,
# not "any shell identifier": nothing else in the provider file is reachable
# through this resolver, the decoy included. A pattern-based check would return
# the decoy's value here.
rc="$(_rc_of "$KEYFILE" HAL_DECOY)"
err="$(_stderr_of "$KEYFILE" HAL_DECOY)"
if [ "$rc" = 1 ] && [[ "$err" != *"$DECOY_SENTINEL"* ]]; then
    ok "(4d) a well-formed name outside the two credentials is refused (exit 1)"
else
    bad "(4d) the resolver served a name outside its two credentials, got exit $rc"
fi

rc="$(_rc_of "$UNPARSABLE" HAL_ID)"
err="$(_stderr_of "$UNPARSABLE" HAL_ID)"
if [ "$rc" = 3 ] && [[ "$err" == *"$UNPARSABLE"* ]]; then
    ok "(4e) an unsourceable keystore exits 3 and names the file"
else
    bad "(4e) unsourceable keystore: expected exit 3 naming the file, got exit $rc"
fi

# A provider file that exits early leaves the extraction subshell at status 0
# with no output. Without a completion marker that is read as "defined but
# empty" — the wrong diagnosis, pointing at the variable instead of the file.
rc="$(_rc_of "$EARLYEXIT" HAL_ID)"
err="$(_stderr_of "$EARLYEXIT" HAL_ID)"
if [ "$rc" = 3 ] && [[ "$err" == *"$EARLYEXIT"* ]]; then
    ok "(4f) a keystore that exits early is diagnosed as a file fault (exit 3), not an empty variable"
else
    bad "(4f) early-exiting keystore: expected exit 3 naming the file, got exit $rc"
fi

rc="$(_rc_of "$MULTILINE" HAL_PASSWORD)"
err="$(_stderr_of "$MULTILINE" HAL_PASSWORD)"
if [ "$rc" = 5 ] && [[ "$err" == *HAL_PASSWORD* ]]; then
    ok "(4g) a multi-line value is refused (exit 5), not silently truncated by the curl config"
else
    bad "(4g) multi-line value: expected exit 5 naming the variable, got exit $rc"
fi

rc="$(_rc_of "$TRAILING_LF" HAL_PASSWORD)"
if [ "$rc" = 5 ]; then
    ok "(4h) a value ending in LF is rejected before command substitution can normalize it"
else
    bad "(4h) trailing-LF credential returned exit $rc, expected 5"
fi
if [[ "$err" == *first-line* || "$err" == *second-line* ]]; then
    bad "(4g) the refusal message disclosed part of the value"
else
    ok "(4g) the refusal message discloses no part of the value"
fi

# --- (5) the keystore file must be a plain, bounded, CR-tolerant file ---------
got="$(_match_in_file "$CRLF" HAL_ID "$ID_SENTINEL")"
if [ "$got" = "MATCH" ]; then
    ok "(5a) a CRLF keystore yields the value without its carriage return"
else
    bad "(5a) a CRLF keystore did not yield a clean value (probe said: $got)"
fi

# A FIFO at the keystore path would block the read forever — an interactive
# deposit hanging with no diagnosis. `timeout` bounds the assertion itself, so
# a regression here fails the suite instead of wedging CI.
if command -v mkfifo >/dev/null && command -v timeout >/dev/null; then
    FIFO="$WORK/fifo.env"
    mkfifo "$FIFO"
    rc=0
    timeout 10 env -i HOME="$FHOME" PATH="$PATH" bash -c \
        '"$1" HAL_ID "$2"' _ "$RESOLVER" "$FIFO" >/dev/null 2>&1 || rc=$?
    if [ "$rc" = 2 ]; then
        ok "(5b) a FIFO at the keystore path is refused (exit 2) instead of blocking"
    elif [ "$rc" = 124 ]; then
        bad "(5b) a FIFO at the keystore path blocked the resolver until the timeout"
    else
        bad "(5b) a FIFO at the keystore path returned exit $rc, expected 2"
    fi
    rm -f "$FIFO"
else
    bad "(5b) mkfifo or timeout is missing — this probe cannot run, so its silence means nothing"
fi

# An oversized keystore is refused before it is sourced, at bash-env.sh's own
# 256 KiB figure. The fixture defines HAL_ID first, so a resolver without the
# cap would happily succeed — the case discriminates.
OVERSIZE="$WORK/oversize.env"
printf 'HAL_ID=%s\n' "$ID_SENTINEL" > "$OVERSIZE"
printf '# %0.spadding' $(seq 1 30000) >> "$OVERSIZE"
if [ "$(wc -c < "$OVERSIZE")" -gt 262144 ]; then
    rc="$(_rc_of "$OVERSIZE" HAL_ID)"
    if [ "$rc" = 2 ]; then
        ok "(5c) an oversized keystore is refused (exit 2) before it is sourced"
    else
        bad "(5c) an oversized keystore returned exit $rc, expected 2"
    fi
else
    bad "(5c) the oversize fixture is below the cap — the case would prove nothing"
fi

echo "--- $(basename "$0"): $fail failing case(s) ---"
exit "$fail"
