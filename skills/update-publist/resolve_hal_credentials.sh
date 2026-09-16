#!/usr/bin/env bash
# Resolve ONE named HAL credential out of the keystore, at point of use.
# Ticket 0944, child of 0942; same pattern as 0393.
#
#   resolve_hal_credentials.sh HAL_ID
#   resolve_hal_credentials.sh HAL_PASSWORD
#
# Prints the value on stdout, alone and with no trailing newline, so the
# documented call is a command substitution into ONE shell variable:
#
#   HAL_ID_VALUE="$(~/.claude/skills/update-publist/resolve_hal_credentials.sh HAL_ID)" || exit 1
#
# The ambient environment is NOT consulted. A pre-set HAL_ID or HAL_PASSWORD has
# no effect here, which is the point: the `KEYS=` selection layer made the
# credential's presence depend on the startup directory (ticket 0360), and the
# deposit then failed as an ordinary HAL auth error one layer away from the real
# cause. Resolving at point of use removes that dependency, and with it the
# cwd-presence probe SKILL.md used to carry.
#
# HYGIENE, NON-NEGOTIABLE: the resolved value goes to stdout and nowhere else.
# It is never logged, never written to a file here, and never placed on an argv
# (`env NAME=value cmd` would expose it to `ps -ef`). Diagnostics on stderr name
# the VARIABLE and the provider FILE only — never a value, and not even the
# rejected argument, since an operator who mistypes the call may have pasted a
# value where a name belongs.
#
# WHY NOT `. hal.env`. Sourcing is not parsing: `.` executes the file's entire
# content in the CURRENT shell, so every variable it defines — not just the two
# wanted — lands in this shell's environment and in every child it spawns
# afterwards. That is precisely the residency ticket 0942 exists to remove, and
# the file holding only two variables today does not move the trust boundary.
# The extraction below sources under `set -a` (the provider file holds bare
# assignments with no `export`) inside `env -i bash -c`, which
#   * drops BASH_ENV, so this child cannot re-source the harness env script;
#   * clears the environment, so the lookup can only resolve a name the provider
#     file itself defines — no ambient variable is smuggled in;
#   * confines every OTHER variable of the file, the decoy case included, to a
#     subshell that dies immediately.
# The extracted value is captured as a string and printed literally, never
# eval'd. Reaching the `.` at all still requires prior write access to the
# keystore, which is the trust boundary the harness already assumes; the
# isolation bounds what such code can reach, it does not stop it running.
# Reference implementation of the same idiom: skills/reviewers/reviewers.sh
# `_keystore_value`.
#
# Exit codes — the taxonomy exists so a PARTIAL resolution (HAL_ID resolves,
# HAL_PASSWORD does not) is diagnosed here rather than as an HAL auth error:
#   0  value printed on stdout
#   1  bad usage or invalid variable name
#   2  provider file missing or unreadable
#   3  provider file could not be sourced
#   4  variable absent, or defined but empty
set -euo pipefail

PROG="resolve_hal_credentials"

if [ "$#" -ne 1 ]; then
    echo "$PROG: usage: resolve_hal_credentials.sh <HAL_ID|HAL_PASSWORD>" >&2
    exit 1
fi

name="$1"
if [[ ! "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "$PROG: the argument is not a valid shell variable name (expected HAL_ID or HAL_PASSWORD)" >&2
    exit 1
fi

# Fixed provider file. HAL_KEYSTORE_FILE is a TEST-ONLY override, same shape as
# REVIEWERS_KEYSTORE: it names a file, never a value.
file="${HAL_KEYSTORE_FILE:-$HOME/.config/keys/hal.env}"

if [ ! -r "$file" ]; then
    echo "$PROG: cannot read the keystore file $file (needed for $name)" >&2
    exit 2
fi

rc=0
value="$(env -i bash -c '
    set -a
    . "$1" >/dev/null 2>&1 || exit 3
    [ -z "${!2+x}" ] && exit 4
    printf "%s" "${!2}"
' _ "$file" "$name")" || rc=$?

case "$rc" in
    0) ;;
    3) echo "$PROG: the keystore file $file could not be sourced (needed for $name)" >&2; exit 3 ;;
    4) echo "$PROG: $name is not defined in $file" >&2; exit 4 ;;
    *) echo "$PROG: unexpected failure (exit $rc) resolving $name from $file" >&2; exit "$rc" ;;
esac

# A defined-but-empty credential would otherwise be a silent-empty success,
# building a half-filled curl config that fails as an HAL auth error.
if [ -z "$value" ]; then
    echo "$PROG: $name is defined but empty in $file" >&2
    exit 4
fi

printf '%s' "$value"
