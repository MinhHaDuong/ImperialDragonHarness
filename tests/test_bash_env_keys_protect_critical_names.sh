#!/usr/bin/env bash
# Tests for the shell/process-critical export-name denylist in the KEYS=
# selection mechanism of scripts/bash-env.sh.
#
# The KEYS= explicit-selection forms (provider:VAR and provider:SRC=DST) let a
# PROJECT-controlled, UNTRUSTED .env choose the EXPORT NAME a value lands under.
# The existing denylist already refuses GUARD_* and _be_* targets. This suite
# guards the extension: a hostile project .env must not be able to overwrite a
# shell/process-critical variable in every subprocess env by aiming the export
# at PATH, BASH_ENV, LD_PRELOAD, IFS, and their kin.
#
# Security property: for a protected export NAME, the entry is REFUSED (skipped
# with a warning), so a pre-existing real value of that variable is NOT
# overwritten (and the variable is not newly injected/exported), and the shell
# survives. Legitimate renames to ordinary names, and the GUARD_/_be_ refusals,
# are unaffected.
#
# Two complementary checks:
#   * denylist completeness — every listed name, aimed at as a rename target,
#     produces the "protected name: <name>" warning and a surviving shell.
#   * non-injection — a pre-seeded real value survives (PATH, LD_PRELOAD), a
#     no-rename form finds-but-refuses a file-defined critical value (BASH_ENV),
#     a prefix-family target is never exported (BASH_FUNC_*, DYLD_*), and IFS is
#     not turned into an exported variable.
#
# Like its sibling suite, this never touches the real ~/.config/keys — it builds
# a FAKE HOME temp dir whose fixtures hold NON-secret sentinel values only.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/bash-env.sh"
fail=0

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

FHOME="$WORK/home"
mkdir -p "$FHOME/.config/keys"
# Provider file: EVIL is the rename-form payload; BASH_ENV lets the no-rename
# form (provider:BASH_ENV) find a value it would inject if not refused.
printf 'EVIL=evilpayload\nHF_TOKEN=hfval\nBASH_ENV=filebashenv\n' \
    > "$FHOME/.config/keys/zzz.env"
printf 'HF_TOKEN=hfval\n' > "$FHOME/.config/keys/huggingface.env"

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

# Load bash-env.sh but PRE-SEED <var>=<realval> in the sourcing shell first, then
# print <var>. A refused KEYS entry leaves the seeded value untouched; an accepted
# one overwrites it.
_load_var_preseed() {
    local home="$1" projdir="$2" var="$3" realval="$4"
    HOME="$home" bash -c '
        cd "$1" || exit 1
        export "$3=$4"
        source "$2"
        n="$3"
        printf "%s" "${!n-}"
    ' _ "$projdir" "$SCRIPT" "$var" "$realval" 2>/dev/null
}

# Load bash-env.sh and return only the exit code (0 = no shell error).
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

_mkproj() {
    local dir="$WORK/$1"
    mkdir -p "$dir"
    printf '%s' "$2" > "$dir/.env"
    printf '%s' "$dir"
}

REAL="REAL_SENTINEL_kept_intact"

# --- (1) denylist completeness: every listed exact name warns + survives ---------
# Rename form KEYS=zzz:EVIL=<NAME>. Because these are inherited normally here (a
# valid PATH etc.), the extraction spawns fine pre-fix, so the "protected name"
# warning is the clean pre/post discriminator.
# The GCONV_PATH + interpreter-var tail (GCONV_PATH, PYTHONPATH, NODE_OPTIONS,
# NODE_PATH, PERL5LIB, RUBYOPT) was added in ticket 0345 when both export paths
# were unified behind the shared _be_is_protected_name predicate; those names go
# RED against a pre-0345 script, which only covered the 0343 head of this list.
# The git/pager exec vectors (GIT_SSH_COMMAND, GIT_SSH, GIT_ASKPASS,
# GIT_EXTERNAL_DIFF, LESSOPEN, LESSCLOSE) were added in the 0345 verify round: the
# harness runs git constantly, so any of these is a direct command-execution
# channel if a hostile project .env can aim a value at it.
for name in PATH BASH_ENV ENV SHELLOPTS BASHOPTS IFS PS1 PS2 PS3 PS4 \
            PROMPT_COMMAND CDPATH GLOBIGNORE LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT \
            GCONV_PATH PYTHONPATH NODE_OPTIONS NODE_PATH PERL5LIB RUBYOPT \
            GIT_SSH_COMMAND GIT_SSH GIT_ASKPASS GIT_EXTERNAL_DIFF \
            LESSOPEN LESSCLOSE; do
    proj="$(_mkproj "p1_$name" "KEYS=zzz:EVIL=$name
")"
    _assert_contains "(1:$name) warns 'protected name: $name'" \
        "$(_load_stderr "$FHOME" "$proj")" "refusing KEYS export to protected name: $name"
    _assert_eq "(1:$name) shell survives (rc 0)" \
        "$(_load_rc "$FHOME" "$proj")" "0"
done

# --- (2) non-injection: pre-seeded PATH survives (valid marker PATH) --------------
# A bogus PATH would break the env/bash the extraction itself needs, so use a
# marker prepended to a working PATH. Pre-fix, PATH is overwritten with the
# payload (marker gone); post-fix, the refusal keeps the marker PATH.
MARKER_PATH="/keys-protect-marker:/usr/bin:/bin"
P2="$(_mkproj p2 'KEYS=zzz:EVIL=PATH
')"
_assert_eq "(2) PATH keeps its marker value (payload refused)" \
    "$(_load_var_preseed "$FHOME" "$P2" PATH "$MARKER_PATH")" "$MARKER_PATH"

# --- (3) non-injection: pre-seeded LD_PRELOAD survives ---------------------------
P3="$(_mkproj p3 'KEYS=zzz:EVIL=LD_PRELOAD
')"
_assert_eq "(3) LD_PRELOAD pre-seeded value retained (payload refused)" \
    "$(_load_var_preseed "$FHOME" "$P3" LD_PRELOAD "$REAL")" "$REAL"

# --- (4) no-rename form: provider:BASH_ENV finds a file value but is refused ------
# SRC == DST == BASH_ENV; the provider file defines BASH_ENV=filebashenv, so
# pre-fix the no-rename form exports it and clobbers the seeded value. The
# export-name refusal must fire before any injection.
P4="$(_mkproj p4 'KEYS=zzz:BASH_ENV
')"
_assert_eq "(4) no-rename BASH_ENV: pre-seeded value retained" \
    "$(_load_var_preseed "$FHOME" "$P4" BASH_ENV "$REAL")" "$REAL"
_assert_contains "(4) no-rename BASH_ENV: warns 'protected name'" \
    "$(_load_stderr "$FHOME" "$P4")" "protected name: BASH_ENV"

# --- (5) prefix families: BASH_FUNC_* and DYLD_* refused (never exported) ---------
# Real BASH_FUNC_ exploit names carry a %% suffix, but that is not a valid
# identifier and never survives the SRC/DST identifier check; a plain
# BASH_FUNC_-prefixed identifier is the reachable case the prefix glob must catch.
P5A="$(_mkproj p5a 'KEYS=zzz:EVIL=BASH_FUNC_evilfn
')"
_assert_not_contains "(5a) BASH_FUNC_ target NOT exported" \
    "$(_load_exports "$FHOME" "$P5A")" "declare -x BASH_FUNC_evilfn"
_assert_contains "(5a) BASH_FUNC_ prefix warns 'protected name'" \
    "$(_load_stderr "$FHOME" "$P5A")" "protected name"
P5B="$(_mkproj p5b 'KEYS=zzz:EVIL=DYLD_INSERT_LIBRARIES
')"
_assert_not_contains "(5b) DYLD_ target NOT exported" \
    "$(_load_exports "$FHOME" "$P5B")" "declare -x DYLD_INSERT_LIBRARIES"
_assert_contains "(5b) DYLD_ prefix warns 'protected name'" \
    "$(_load_stderr "$FHOME" "$P5B")" "protected name"

# --- (6) IFS must not become an exported variable --------------------------------
# The script restores IFS to the caller's value at loop end, so its VALUE is not a
# clean discriminator; but pre-fix `export IFS=...` sets IFS's export attribute,
# leaking it to every child. Post-fix the refusal means IFS is never exported.
P6="$(_mkproj p6 'KEYS=zzz:EVIL=IFS
')"
_assert_not_contains "(6) IFS is NOT turned into an exported variable" \
    "$(_load_exports "$FHOME" "$P6")" "declare -x IFS"

# --- (7) regressions: legit rename works; whole-file source works; GUARD_/_be_ ---
# 7a: an ordinary DST still works.
P7A="$(_mkproj p7a 'KEYS=zzz:EVIL=MY_ORDINARY_KEY
')"
_assert_eq "(7a) legit rename to ordinary DST still works" \
    "$(_load_var "$FHOME" "$P7A" MY_ORDINARY_KEY)" "evilpayload"
# 7b: a bare provider whole-file source still works.
P7B="$(_mkproj p7b 'KEYS=huggingface
')"
_assert_eq "(7b) bare provider whole-file source still works" \
    "$(_load_var "$FHOME" "$P7B" HF_TOKEN)" "hfval"
# 7c: GUARD_ target still refused.
P7C="$(_mkproj p7c 'KEYS=zzz:EVIL=GUARD_ALLOW_PRIMARY_EDIT
')"
_assert_eq "(7c) GUARD_ target still refused" \
    "$(_load_var "$FHOME" "$P7C" GUARD_ALLOW_PRIMARY_EDIT)" ""
# 7d: _be_ target still refused.
P7D="$(_mkproj p7d 'KEYS=zzz:EVIL=_be_ifs
')"
_assert_eq "(7d) _be_ target still refused" \
    "$(_load_var "$FHOME" "$P7D" _be_ifs)" ""

exit "$fail"
