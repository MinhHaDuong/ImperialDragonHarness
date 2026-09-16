#!/usr/bin/env bash
# Resolve ONE named HAL credential out of the keystore, at point of use.
# Ticket 0944, child of 0942; same pattern as 0393.
#
#   resolve_hal_credentials.sh HAL_ID
#   resolve_hal_credentials.sh HAL_PASSWORD
#   resolve_hal_credentials.sh HAL_ID <keystore-file>   # tests only
#
# Prints the value on stdout, alone and with no trailing newline, so the
# documented call is a command substitution into ONE shell variable:
#
#   HAL_ID_VALUE="$(~/.claude/skills/update-publist/resolve_hal_credentials.sh HAL_ID)" || exit $?
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
# WHY THE PROVIDER FILE IS AN ARGUMENT AND NOT AN ENVIRONMENT OVERRIDE.
# The obvious shape is a `HAL_KEYSTORE_FILE` variable honoured "for tests only",
# as `REVIEWERS_KEYSTORE` is. Nothing enforces such a label: the protected-name
# predicate of the harness env loader (~/.claude/scripts/bash-env.sh,
# `_be_is_protected_name`) does not list it, so an UNTRUSTED project `.env` — the
# threat model that loader is built around — could point this resolver at a file
# of its choosing, and the `.` below would then execute it. A second positional
# argument cannot be set ambiently: it has to be written into the call, which is
# fixed prose in SKILL.md. (What remains, unchanged by this script, is the
# harness-wide assumption that `$HOME` is honest — bash-env.sh resolves its own
# keystore under it too.) The path is not a secret, so argv is the right place
# for it; a VALUE never goes there.
#
# Exit codes — the taxonomy exists so a PARTIAL resolution (HAL_ID resolves,
# HAL_PASSWORD does not) is diagnosed here rather than as an HAL auth error:
#   0  value printed on stdout
#   1  bad usage or invalid variable name
#   2  provider file missing, unreadable, not a regular file, or over the size cap
#   3  provider file could not be sourced, or did not run to completion
#   4  variable absent, or defined but empty
#   5  value is not a single line, so it cannot be carried by a curl -K config
set -euo pipefail
# So the size check below counts BYTES, not multibyte characters.
export LC_ALL=C

PROG="resolve_hal_credentials"
# No legitimate .env approaches this; the cap is what stops a pathological or
# adversarial file being read at all, and it is bash-env.sh's own figure.
MAX_KEYSTORE_BYTES=262144

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "$PROG: usage: resolve_hal_credentials.sh <HAL_ID|HAL_PASSWORD> [keystore-file]" >&2
    exit 1
fi

# An ALLOWLIST, not a shell-identifier pattern. This resolver is the HAL
# deposit's credential step, not a general keystore reader: the two names it
# serves are the two the deposit needs, and nothing in the provider file — the
# decoy of the test fixture included — is reachable through it. A pattern would
# have matched whatever the caller asked for, which is a wider surface than the
# skill has any use for.
name="$1"
case "$name" in
    HAL_ID|HAL_PASSWORD) ;;
    *)  echo "$PROG: unknown credential; this resolver serves HAL_ID and HAL_PASSWORD only" >&2
        exit 1 ;;
esac

file="${2:-$HOME/.config/keys/hal.env}"

# `-f` before anything that reads: a FIFO at the keystore path would block the
# size check and then the source, hanging an interactive deposit with no
# diagnosis at all. A named pipe, a directory or a device is not a keystore.
if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    echo "$PROG: cannot read the keystore file $file as a regular file (needed for $name)" >&2
    exit 2
fi

# The cap is enforced with a BUILTIN, deliberately. `wc -c` resolves through
# PATH, so a shim `wc` earlier on it would defeat the very guard this line
# exists to be — and an absolute `/usr/bin/wc` only trades that for a path that
# is not the same on every system. `read -N` is bash's own, so neither problem
# arises: read one byte past the cap and see whether that many arrived.
# (`-f` above already guarantees this cannot block on a FIFO.)
oversize=""
read -r -N "$((MAX_KEYSTORE_BYTES + 1))" oversize < "$file" || true
if [ "${#oversize}" -gt "$MAX_KEYSTORE_BYTES" ]; then
    echo "$PROG: the keystore file $file exceeds the size cap (${MAX_KEYSTORE_BYTES} bytes), refusing to source it (needed for $name)" >&2
    exit 2
fi
unset -v oversize

# NOT done here, and worth saying why rather than adding a line that looks like
# a mitigation: `unset -v BASH_ENV ENV` at this point protects nothing. A
# hostile BASH_ENV has already run, before line 1, and the one child this script
# spawns is under `env -i`, which drops both. The precondition for either is a
# calling shell that is already compromised — the state the harness env loader
# exists to prevent, and which no line in this file could recover from.

# The leading `v` is a completion marker, not decoration. A provider file that
# calls `exit 0` — or any other early exit from the sourced code — ends the
# subshell with status 0 and no output, which is indistinguishable from a
# successfully extracted empty string. The marker separates the two: no marker
# means the extraction never reached its own printf.
rc=0
marked="$(env -i bash -c '
    set -a
    . "$1" >/dev/null 2>&1 || exit 3
    [ -z "${!2+x}" ] && exit 4
    printf "v%s" "${!2}"
' _ "$file" "$name")" || rc=$?

case "$rc" in
    0) ;;
    3) echo "$PROG: the keystore file $file could not be sourced (needed for $name)" >&2; exit 3 ;;
    4) echo "$PROG: $name is not defined in $file" >&2; exit 4 ;;
    *) echo "$PROG: unexpected failure (exit $rc) resolving $name from $file" >&2; exit "$rc" ;;
esac

if [ -z "$marked" ]; then
    echo "$PROG: the keystore file $file did not run to completion (needed for $name)" >&2
    exit 3
fi

value="${marked#v}"
# A CRLF provider file would otherwise append a carriage return to the value and
# corrupt the curl config in a way that reads as an HAL auth error. bash-env.sh
# strips CR for the same reason.
value="${value%$'\r'}"

# A defined-but-empty credential would otherwise be a silent-empty success,
# building a half-filled curl config that fails as an HAL auth error.
if [ -z "$value" ]; then
    echo "$PROG: $name is defined but empty in $file" >&2
    exit 4
fi

# A `curl -K` config is parsed one directive per LINE, so an embedded newline
# would split the value: the password silently truncates at the break and its
# tail is read as a curl directive. Quoting and backslash-escaping in the
# caller do not reach this — the line boundary is below the quoting layer.
# Refusing here rather than escaping there is the fix with the right blast
# radius: one check, at the single point every caller goes through, and the
# failure names the variable instead of arriving as an HAL auth error. No
# credential this skill deposits is multi-line; if one ever is, the config file
# is the wrong carrier for it and that decision belongs to the author.
case "$value" in
    *$'\n'*|*$'\r'*)
        echo "$PROG: $name from $file spans more than one line, which a curl -K config cannot carry" >&2
        exit 5 ;;
esac

printf '%s' "$value"
