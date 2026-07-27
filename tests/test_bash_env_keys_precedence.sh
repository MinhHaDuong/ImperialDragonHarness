#!/usr/bin/env bash
# Precedence between a harness KEYS= and a project KEYS= (tickets 0360, 0361).
#
# DECIDED RULE (0360): a project KEYS= REPLACES the harness KEYS= in
# ~/.claude/.env; it does not compose with it. A project KEYS= line is that
# project's COMPLETE declaration of what it may load, which is what lets a
# project narrow. The harness KEYS= is the selection for directories that
# declare none.
#
# The rule was chosen over union because ~/.claude/.env is sourced before any
# cwd is consulted, so under union the harness selection would become a global
# floor no project could narrow — strictly more exposure, and default-broad
# where the mechanism's invariant is default-deny.
#
# Its cost is that the harness selection vanishes with no signal, and the
# symptom surfaces later as an ordinary auth error in whatever tool wanted the
# credential. So bash-env.sh can name the dropped providers (0361) — on demand,
# under KEYS_EXPLAIN=1.
#
# This suite pins both halves: the precedence itself, and the diagnostic. Most
# of the diagnostic's cases assert SILENCE, and the load-bearing one is that it
# says nothing by DEFAULT. This script is sourced on every subprocess, and under
# the decided rule a project that narrows is doing the correct thing — an
# unconditional line would warn about correct configuration on every command in
# every project that declares a selection, which is how a diagnostic becomes
# noise everybody filters. There is live precedent: an unrelated always-on
# bash-env warning already breaks tests/test_guard_cd_primary_repo.sh on a
# machine whose keystore lacks one selected provider.
#
# Hermetic per rules/coding-bash.md: a real `bash -c` subprocess under a fake
# HOME. The keystore fixtures hold NON-secret sentinel values only — a test
# that needs a real credential to pass is a test that will one day print one.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/bash-env.sh"
fail=0

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

FHOME="$WORK/home"
mkdir -p "$FHOME/.claude" "$FHOME/.config/keys"
printf 'HAL_ID=sentinel-id\nHAL_PASSWORD=sentinel-pw\n' > "$FHOME/.config/keys/hal.env"
printf 'OPENALEX_API_KEY=sentinel-oa\n'                 > "$FHOME/.config/keys/openalex.env"
printf 'ZENODO_TOKEN=sentinel-zn\n'                     > "$FHOME/.config/keys/zenodo.env"

# Set the harness-level selection (or clear it when $1 is empty).
_set_harness_keys() {
    if [ -z "$1" ]; then
        : > "$FHOME/.claude/.env"
    else
        printf 'KEYS=%s\n' "$1" > "$FHOME/.claude/.env"
    fi
}

# Build a project dir whose .env is exactly $2 (empty string = .env with no
# KEYS line), and echo its path.
_mkproj() {
    local name="$1" body="$2" dir="$WORK/$1"
    mkdir -p "$dir"
    printf '%s' "$body" > "$dir/.env"
    printf '%s' "$dir"
}

# Load bash-env.sh the way a real subprocess does — through BASH_ENV, from a
# known-empty base environment, with cwd already at the project dir so $PWD/.env
# is the one under test.
#
# `env -i` is load-bearing here, not ceremony. Without it the subprocess
# inherits the CALLER's BASH_ENV, which on a live harness points at the real
# scripts/bash-env.sh: it would run once at shell startup and export provider
# credentials before the test ever loaded the copy under test, so a variable
# left over from that pass reads as a pass. The first draft of this suite hit
# exactly that and reported the replace rule as broken (rules/coding-bash.md
# § BASH_ENV / hook scripts).
#
# PATH is restored because bash-env.sh shells out to realpath and wc.

# Print the value of env var $3 after loading bash-env.sh from cwd $2. stderr dropped.
_load_var() {
    local home="$1" projdir="$2" var="$3"
    ( cd "$projdir" || exit 1
      env -i HOME="$home" PATH="/usr/bin:/bin" BASH_ENV="$SCRIPT" \
          bash -c 'n="$1"; printf "%s" "${!n-}"' _ "$var" 2>/dev/null )
}

# Print only what bash-env.sh wrote to stderr when loaded from cwd $2, with the
# drop diagnostic requested (KEYS_EXPLAIN=1).
_load_stderr() {
    local home="$1" projdir="$2"
    ( cd "$projdir" || exit 1
      env -i HOME="$home" PATH="/usr/bin:/bin" BASH_ENV="$SCRIPT" KEYS_EXPLAIN=1 \
          bash -c ':' 2>&1 >/dev/null )
}

# Same, but WITHOUT asking for the diagnostic — the default path every ordinary
# subprocess takes.
_load_stderr_default() {
    local home="$1" projdir="$2"
    ( cd "$projdir" || exit 1
      env -i HOME="$home" PATH="/usr/bin:/bin" BASH_ENV="$SCRIPT" \
          bash -c ':' 2>&1 >/dev/null )
}

_check() {
    local label="$1" got="$2" want="$3"
    if [ "$got" = "$want" ]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — expected [$want], got [$got]" >&2
        fail=$((fail + 1))
    fi
}

_check_contains() {
    local label="$1" got="$2" needle="$3"
    if printf '%s' "$got" | grep -qF -- "$needle"; then
        echo "PASS: $label"
    else
        echo "FAIL: $label — expected output containing [$needle], got [$got]" >&2
        fail=$((fail + 1))
    fi
}

_check_no_warning() {
    local label="$1" got="$2"
    if printf '%s' "$got" | grep -qF -- 'replaced the harness selection'; then
        echo "FAIL: $label — expected silence, got [$got]" >&2
        fail=$((fail + 1))
    else
        echo "PASS: $label"
    fi
}

# --- 1. The decided rule: a project KEYS= replaces the harness one -----------
_set_harness_keys 'hal:HAL_ID,hal:HAL_PASSWORD'
PROJ_OTHER="$(_mkproj proj-other 'KEYS=openalex:OPENALEX_API_KEY
')"

_check "project KEYS= wins: its own provider resolves" \
    "$(_load_var "$FHOME" "$PROJ_OTHER" OPENALEX_API_KEY)" 'sentinel-oa'
_check "project KEYS= replaces: harness HAL_ID does not resolve" \
    "$(_load_var "$FHOME" "$PROJ_OTHER" HAL_ID)" ''
_check "project KEYS= replaces: harness HAL_PASSWORD does not resolve" \
    "$(_load_var "$FHOME" "$PROJ_OTHER" HAL_PASSWORD)" ''

# --- 2. The harness selection applies where a project declares none ----------
PROJ_NOKEYS="$(_mkproj proj-nokeys 'SOME_SETTING=1
')"
_check "no project KEYS=: harness selection still resolves" \
    "$(_load_var "$FHOME" "$PROJ_NOKEYS" HAL_ID)" 'sentinel-id'

# --- 3. The diagnostic is OPT-IN --------------------------------------------
# The load-bearing case. bash-env.sh is sourced on every subprocess, and under
# the decided rule a project that narrows is doing the correct thing, so an
# unconditional line would warn about correct configuration on every command in
# every project that declares a selection. Silence by default is the guarantee
# that keeps this diagnostic worth reading when it does fire.
_check_no_warning "silent by default: a drop says nothing without KEYS_EXPLAIN" \
    "$(_load_stderr_default "$FHOME" "$PROJ_OTHER")"

# --- 4. Asked for, it names the dropped providers (0361) --------------------
_check_contains "drop is reported" \
    "$(_load_stderr "$FHOME" "$PROJ_OTHER")" 'replaced the harness selection'
_check_contains "drop names the dropped provider" \
    "$(_load_stderr "$FHOME" "$PROJ_OTHER")" 'dropped: hal'

# The warning must never carry a value, only names.
STDERR_OTHER="$(_load_stderr "$FHOME" "$PROJ_OTHER")"
if printf '%s' "$STDERR_OTHER" | grep -qE 'sentinel-(id|pw|oa|zn)'; then
    echo "FAIL: warning leaked a credential value" >&2
    fail=$((fail + 1))
else
    echo "PASS: warning carries names only, no value"
fi

# Two dropped providers are both named.
_set_harness_keys 'hal:HAL_ID,zenodo:ZENODO_TOKEN'
_check_contains "both dropped providers named" \
    "$(_load_stderr "$FHOME" "$PROJ_OTHER")" 'dropped: hal,zenodo'

# --- 5. The four silent cases (even with the diagnostic requested) ----------
_set_harness_keys 'hal:HAL_ID'

_check_no_warning "no project KEYS= at all" \
    "$(_load_stderr "$FHOME" "$PROJ_NOKEYS")"

PROJ_SAME="$(_mkproj proj-same 'KEYS=hal:HAL_ID
')"
_check_no_warning "identical selections" \
    "$(_load_stderr "$FHOME" "$PROJ_SAME")"

PROJ_SUPER="$(_mkproj proj-super 'KEYS=hal:HAL_ID,openalex:OPENALEX_API_KEY
')"
_check_no_warning "project selection is a superset" \
    "$(_load_stderr "$FHOME" "$PROJ_SUPER")"

# A project naming the same provider with a different selector keeps the
# provider in force, so there is no provider-level drop to report.
PROJ_SAMEPROV="$(_mkproj proj-sameprov 'KEYS=hal:HAL_PASSWORD
')"
_check_no_warning "same provider, different selector" \
    "$(_load_stderr "$FHOME" "$PROJ_SAMEPROV")"

_set_harness_keys ''
_check_no_warning "no harness KEYS= at all" \
    "$(_load_stderr "$FHOME" "$PROJ_OTHER")"

# --- 6. Bookkeeping variables must not leak into the subprocess -------------
_set_harness_keys 'hal:HAL_ID'
_check "harness-KEYS bookkeeping var does not leak" \
    "$(_load_var "$FHOME" "$PROJ_OTHER" _be_harness_keys)" ''
_check "explain-flag bookkeeping var does not leak" \
    "$(_load_var "$FHOME" "$PROJ_OTHER" _be_explain)" ''

if [ "$fail" -ne 0 ]; then
    echo "FAILED: $fail check(s)" >&2
    exit 1
fi
echo "OK: KEYS precedence and drop-reporting behave as decided (ticket 0360/0361)"
