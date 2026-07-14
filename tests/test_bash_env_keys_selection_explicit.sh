#!/usr/bin/env bash
# Tests for EXPLICIT per-key selection and rename in the KEYS= mechanism of
# scripts/bash-env.sh.
#
# In addition to the bare `provider` form (source the whole
# $HOME/.config/keys/<provider>.env), a KEYS= entry may select a single variable:
#
#   provider          -> source the whole provider file (unchanged behaviour)
#   provider:VAR      -> export ONLY VAR from the provider file, under name VAR
#   provider:SRC=DST  -> export ONLY SRC from the provider file, renamed to DST
#
# The security property under test: a `provider:` selection entry must NOT drop
# the provider file's OTHER variables into the environment. A provider file may
# hold several keysets (openrouter.env: OPENROUTER_API_KEY_AEDIST,
# OPENROUTER_API_KEY_KIEU, EXPIRED_*); selecting one must leave the siblings
# behind. The file is sourced in an isolated subshell, only the requested value
# is extracted, and it is assigned LITERALLY (never eval'd) so a value with
# spaces or a $(...) literal is preserved verbatim, never executed.
#
# This suite never touches the real ~/.config/keys — it builds a FAKE HOME temp
# dir whose fixtures hold NON-secret sentinel values only.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/bash-env.sh"
fail=0

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Fake HOME with ~/.config/keys/ provider fixtures — NON-secret sentinels only.
FHOME="$WORK/home"
mkdir -p "$FHOME/.config/keys"
# A multi-key provider file: selecting one key must not export the siblings.
printf 'OPENROUTER_API_KEY_AEDIST=aedistval\nOPENROUTER_API_KEY_KIEU=kieuval\nEXPIRED_OPENROUTER_API_KEY=expiredval\n' \
    > "$FHOME/.config/keys/openrouter.env"
# A provider file with a token plus an unrelated var.
printf 'ZENODO_TOKEN=ztok\nZENODO_OTHER=zother\n' > "$FHOME/.config/keys/zenodo.env"
# A whole-file-source regression fixture.
printf 'HF_TOKEN=hfval\n' > "$FHOME/.config/keys/huggingface.env"
# A provider file whose value carries a space and a $(...) LITERAL — stored
# single-quoted so sourcing the (trusted) file yields the literal string; the
# parent must then export it verbatim, never re-evaluating the $(...).
printf "TRICKY_KEY='a b \$(touch %s/PWNED) c'\n" "$WORK" > "$FHOME/.config/keys/tricky.env"

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

# Load bash-env.sh as above and print only its STDERR (the diagnostic warnings),
# discarding stdout. `2>&1 >/dev/null`: send stderr to the capture, then stdout to
# the void — so $( ) collects exactly the warnings the script emits.
_load_stderr() {
    local home="$1" projdir="$2"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        source "$2"
    ' _ "$projdir" "$SCRIPT" 2>&1 >/dev/null
}

# Load bash-env.sh as above and print `export -p` (the exported environment).
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

# Load bash-env.sh with an EXTRA variable pre-exported into the parent env, then
# print the value of <var>. Proves the extraction subshell cannot resolve a SRC
# name against the ambient environment (only against the provider file).
_load_var_ambient() {
    local home="$1" projdir="$2" var="$3" amb_name="$4" amb_val="$5"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        export "$4=$5"
        source "$2"
        n="$3"
        printf "%s" "${!n-}"
    ' _ "$projdir" "$SCRIPT" "$var" "$amb_name" "$amb_val" 2>/dev/null
}

# Make a project dir <name> holding <env-content> as its .env; echo the dir path.
_mkproj() {
    local dir="$WORK/$1"
    mkdir -p "$dir"
    printf '%s' "$2" > "$dir/.env"
    printf '%s' "$dir"
}

# --- (1) provider:SRC=DST selects and renames; siblings do NOT leak -------------
P1="$(_mkproj p1 'KEYS=openrouter:OPENROUTER_API_KEY_AEDIST=OPENROUTER_API_KEY
')"
_assert_eq "(1) DST holds the selected value" \
    "$(_load_var "$FHOME" "$P1" OPENROUTER_API_KEY)" "aedistval"
_assert_eq "(1) sibling KIEU is NOT set" \
    "$(_load_var "$FHOME" "$P1" OPENROUTER_API_KEY_KIEU)" ""
_assert_eq "(1) source name is NOT set (only DST exported)" \
    "$(_load_var "$FHOME" "$P1" OPENROUTER_API_KEY_AEDIST)" ""
_assert_eq "(1) EXPIRED_* sibling is NOT set" \
    "$(_load_var "$FHOME" "$P1" EXPIRED_OPENROUTER_API_KEY)" ""
# Export-boundary proof: only DST is marked for export. Match the `declare -x
# NAME` form, not a bare substring — the KEYS value itself is exported and
# literally contains "OPENROUTER_API_KEY_AEDIST", which would false-match.
P1_EXPORTS="$(_load_exports "$FHOME" "$P1")"
_assert_contains "(1) DST IS exported" "$P1_EXPORTS" "declare -x OPENROUTER_API_KEY="
_assert_not_contains "(1) SRC name is NOT exported" \
    "$P1_EXPORTS" "declare -x OPENROUTER_API_KEY_AEDIST"
_assert_not_contains "(1) KIEU is NOT exported" \
    "$P1_EXPORTS" "declare -x OPENROUTER_API_KEY_KIEU"

# --- (2) provider:VAR selects without renaming; other vars not exported ---------
P2="$(_mkproj p2 'KEYS=zenodo:ZENODO_TOKEN
')"
_assert_eq "(2) selected VAR is exported under its own name" \
    "$(_load_var "$FHOME" "$P2" ZENODO_TOKEN)" "ztok"
_assert_eq "(2) other var in file is NOT exported" \
    "$(_load_var "$FHOME" "$P2" ZENODO_OTHER)" ""

# --- (3) bare provider still whole-file sources (regression) ---------------------
P3="$(_mkproj p3 'KEYS=huggingface
')"
_assert_eq "(3) bare provider whole-file sources (HF_TOKEN)" \
    "$(_load_var "$FHOME" "$P3" HF_TOKEN)" "hfval"

# --- (4) mixed line: whole, :VAR, and :SRC=DST all resolve ----------------------
P4="$(_mkproj p4 'KEYS=huggingface,zenodo:ZENODO_TOKEN,openrouter:OPENROUTER_API_KEY_AEDIST=OPENROUTER_API_KEY
')"
_assert_eq "(4) whole-file HF_TOKEN loads" \
    "$(_load_var "$FHOME" "$P4" HF_TOKEN)" "hfval"
_assert_eq "(4) :VAR ZENODO_TOKEN loads" \
    "$(_load_var "$FHOME" "$P4" ZENODO_TOKEN)" "ztok"
_assert_eq "(4) :SRC=DST OPENROUTER_API_KEY loads" \
    "$(_load_var "$FHOME" "$P4" OPENROUTER_API_KEY)" "aedistval"
_assert_eq "(4) KIEU sibling absent" \
    "$(_load_var "$FHOME" "$P4" OPENROUTER_API_KEY_KIEU)" ""

# --- (5) invalid entries are skipped with a warning; shell survives -------------
# SRC with a dash (invalid identifier).
P5A="$(_mkproj p5a 'KEYS=openrouter:bad-name=OPENROUTER_API_KEY
')"
_assert_eq "(5a) invalid SRC: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P5A")" "0"
_assert_eq "(5a) invalid SRC: DST not set" \
    "$(_load_var "$FHOME" "$P5A" OPENROUTER_API_KEY)" ""
_assert_contains "(5a) invalid SRC: warns 'ignoring invalid KEYS entry'" \
    "$(_load_stderr "$FHOME" "$P5A")" "ignoring invalid KEYS entry"
# Provider with traversal chars.
P5B="$(_mkproj p5b 'KEYS=../x:Y
')"
_assert_eq "(5b) traversal provider: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P5B")" "0"
_assert_eq "(5b) traversal provider: Y not set" \
    "$(_load_var "$FHOME" "$P5B" Y)" ""
# Too many =: SRC=DST=extra.
P5C="$(_mkproj p5c 'KEYS=openrouter:OPENROUTER_API_KEY_AEDIST=DST=extra
')"
_assert_eq "(5c) SRC=DST=extra: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P5C")" "0"
_assert_eq "(5c) SRC=DST=extra: DST not set" \
    "$(_load_var "$FHOME" "$P5C" DST)" ""
_assert_eq "(5c) SRC=DST=extra: aedist value not smuggled anywhere" \
    "$(_load_var "$FHOME" "$P5C" OPENROUTER_API_KEY)" ""

# --- (5d) named SRC absent from the file -> warn + skip, shell survives ----------
P5D="$(_mkproj p5d 'KEYS=openrouter:NOPE=OPENROUTER_API_KEY
')"
_assert_eq "(5d) absent SRC: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P5D")" "0"
_assert_eq "(5d) absent SRC: DST not set" \
    "$(_load_var "$FHOME" "$P5D" OPENROUTER_API_KEY)" ""
_assert_contains "(5d) absent SRC: warns 'KEYS var not found'" \
    "$(_load_stderr "$FHOME" "$P5D")" "KEYS var not found"

# --- (6) value integrity: spaces and $(...) exported verbatim, NOT executed ------
rm -f "$WORK/PWNED"
P6="$(_mkproj p6 'KEYS=tricky:TRICKY_KEY=TRICKY_OUT
')"
_assert_eq "(6) value with space and \$(...) exported verbatim" \
    "$(_load_var "$FHOME" "$P6" TRICKY_OUT)" 'a b $(touch '"$WORK"'/PWNED) c'
# The $(...) must NOT have been executed at any point.
if [ -e "$WORK/PWNED" ]; then
    echo "FAIL: (6) command substitution in value was EXECUTED (PWNED created)"
    fail=1
else
    echo "PASS: (6) command substitution in value was NOT executed"
fi

# --- (7) ambient-env leak: SRC absent from the file but present as an exported
#         ambient var must NOT be resolved — the subshell sees a cleared env ------
# SRC=AMBIENT_SENTINEL is not defined by zenodo.env, but we pre-export it into the
# parent with a sentinel value. A leaking extraction subshell would inherit it and
# smuggle the ambient value into DST; the env -i subshell cannot see it, so DST
# stays unset and the shell survives.
P7="$(_mkproj p7 'KEYS=zenodo:AMBIENT_SENTINEL=DEST_VAR
')"
_assert_eq "(7) ambient SRC does not leak into DST" \
    "$(_load_var_ambient "$FHOME" "$P7" DEST_VAR AMBIENT_SENTINEL leakval)" ""
_assert_eq "(7) ambient-leak entry: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P7")" "0"

# --- (8) DST forging a guard var is refused (default-deny) -----------------------
# An untrusted project .env must not be able to name GUARD_* / _GUARD_* as the
# export target — that would forge a per-process guard nonce or the worktree-path
# override honored by pretooluse-worktree-path-guard.sh.
P8A="$(_mkproj p8a 'KEYS=huggingface:HF_TOKEN=GUARD_ALLOW_PRIMARY_EDIT
')"
_assert_eq "(8a) GUARD_ dst: not set" \
    "$(_load_var "$FHOME" "$P8A" GUARD_ALLOW_PRIMARY_EDIT)" ""
_assert_eq "(8a) GUARD_ dst: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P8A")" "0"
P8B="$(_mkproj p8b 'KEYS=huggingface:HF_TOKEN=_GUARD_WORKTREE_ROOT
')"
_assert_eq "(8b) _GUARD_ override dst: not set" \
    "$(_load_var "$FHOME" "$P8B" _GUARD_WORKTREE_ROOT)" ""
_assert_eq "(8b) _GUARD_ override dst: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P8B")" "0"

# --- (9) DST clobbering this script's own _be_* bookkeeping is refused -----------
# `_be_ifs` is live loop state in the sourcing shell; letting an untrusted .env set
# it mid-run would corrupt the KEYS parse. Reject the entry.
P9="$(_mkproj p9 'KEYS=huggingface:HF_TOKEN=_be_ifs
')"
_assert_eq "(9) _be_* dst: not leaked into the env" \
    "$(_load_var "$FHOME" "$P9" _be_ifs)" ""
_assert_eq "(9) _be_* dst: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P9")" "0"

# --- (10) missing provider file -> warn 'KEYS provider not found' -----------------
# A valid provider NAME whose file does not exist: the file-existence check fires
# before any subshell and must warn the file-missing diagnostic.
P10="$(_mkproj p10 'KEYS=ghostprovider
')"
_assert_contains "(10) missing provider: warns 'KEYS provider not found'" \
    "$(_load_stderr "$FHOME" "$P10")" "KEYS provider not found"

# --- (11) provider file present but source fails -> distinct rc=3 diagnostic ------
# broken.env is a valid provider file NAME whose CONTENT has a syntax error (an
# unterminated array assignment), so the extraction subshell's `. "$file"` fails
# (exit 3) — a condition distinct from a MISSING file. The two must produce
# DIFFERENT warnings: rc=3 says "could not read", NOT "provider not found".
printf 'FOO=(\n' > "$FHOME/.config/keys/broken.env"
P11="$(_mkproj p11 'KEYS=broken:SOMEVAR=DST
')"
_assert_eq "(11) source-failed: DST not set" \
    "$(_load_var "$FHOME" "$P11" DST)" ""
_assert_eq "(11) source-failed: shell survives (rc 0)" \
    "$(_load_rc "$FHOME" "$P11")" "0"
P11_ERR="$(_load_stderr "$FHOME" "$P11")"
_assert_contains "(11) source-failed: warns 'could not read'" \
    "$P11_ERR" "could not read"
_assert_not_contains "(11) source-failed: NOT the file-missing message" \
    "$P11_ERR" "KEYS provider not found"

exit "$fail"
