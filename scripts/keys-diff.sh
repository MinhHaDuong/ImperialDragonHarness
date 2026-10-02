#!/usr/bin/env bash
# keys-diff — compare this machine's keystore with another host's, by NAME
# and FINGERPRINT only (ticket 0937).
#
#   scripts/keys-diff.sh <host>
#
# ~/.config/keys/*.env holds this fleet's credentials, one file per provider,
# copied by hand to each machine. A key rotated on one machine and not another
# is invisible until a consumer silently degrades — and the consumers are
# fail-open by design, so nothing downstream ever surfaces it. This script
# reports, for each provider file, which variable names each side defines and
# whether the values agree — by sha256[:12] fingerprint, never by value.
#
# INVARIANT, from the ticket: no credential value is ever printed, logged, or
# transmitted. Everything this script emits — records, comparisons, errors —
# carries names and fingerprints only. The value exists inside one `env -i`
# child per fingerprint and leaves it as 12 hex characters; the child's stdout
# is a pipe into sha256sum, never a terminal, a file, or an argv.
#
# THE REMOTE RUNS THIS SAME FILE. The script pipes itself over stdin to
# `bash -s -- --scan` on the host, which scans the remote's own
# $HOME/.config/keys and prints the same record format. Both sides therefore
# run the identical scanner function; only the directory differs.
#
# A check whose all-clear is indistinguishable from "I could not look" is not
# a check: any ssh or keystore failure is LOUD, names the host on stderr, and
# exits 2 — never reported as agreement.
#
# Knobs (exist for the tests; production defaults shown). KEYS_DIFF_SSH is
# invoked UNQUOTED so the multi-word default word-splits into argv words
# (pattern from skills/reviewers/padme-reviewers.sh).
#   KEYS_DIFF_LOCAL_DIR  local keystore directory ($HOME/.config/keys)
#   KEYS_DIFF_SSH       ssh invocation (ssh -F $HOME/.ssh/config -o BatchMode=yes)
#
# Exit codes: 0 agree, 1 divergence, 2 could-not-look (ssh or keystore
# failure, or bad usage).
set -euo pipefail
# Byte-exact size counting below (the cap check counts characters, and with
# LC_ALL=C a character is a byte), and deterministic grep behavior.
export LC_ALL=C

KEYS_DIFF_LOCAL_DIR="${KEYS_DIFF_LOCAL_DIR:-$HOME/.config/keys}"
KEYS_DIFF_SSH="${KEYS_DIFF_SSH:-ssh -F "$HOME/.ssh/config" -o BatchMode=yes}"

# --- the scanner (identical on both machines) ---------------------------------
# Emits records `file|name|fingerprint` per line — `|`-delimited, never tab:
# tab is IFS whitespace, so an empty middle field would shift every later
# field left (rules/coding-bash.md). The fingerprint is computed in an `env -i`
# child (the ticket-0944 resolver discipline): a cleared environment means an
# ambient value of the same name can never satisfy or poison the lookup, and
# every other variable the provider file defines is confined to a subshell
# that dies immediately. `set -a` because the provider files hold bare
# assignments with no `export`.
scan_keystore() {  # $1 = keystore directory; prints file|name|fingerprint records
    local dir="$1" f name fp oversize
    [ -d "$dir" ] || return 1
    for f in "$dir"/*.env; do
        [ -e "$f" ] || continue
        # Refuse before reading, the 0944 resolver discipline: a FIFO or
        # device would block the open, a directory makes grep fail into
        # silence (no records, no error — agreement over a file never
        # looked at), and an unbounded read is how a pathological file
        # reaches the source step at all.
        if [ ! -f "$f" ] || [ ! -r "$f" ]; then
            echo "keys-diff: $f is not a readable regular file, refusing to scan it" >&2
            return 2
        fi
        # Size cap at bash-env.sh's own 256 KiB figure, counted with a
        # builtin (LC_ALL=C is exported above, so characters are bytes):
        # `wc -c` resolves through PATH, so a shim earlier on it would
        # defeat the very guard this line exists to be.
        oversize=""
        read -r -N 262145 oversize < "$f" || true
        if [ "${#oversize}" -gt 262144 ]; then
            echo "keys-diff: $f exceeds the size cap (262144 bytes), refusing to scan it" >&2
            return 2
        fi
        unset -v oversize
        # Names only, from the assignment lines: `grep -oE` matches the exact
        # variable-declaration prefix, `tr` strips the `=`.
        while IFS= read -r name; do
            [ -n "$name" ] || continue
            # The child's stdin is /dev/null so a provider file that reads
            # stdin cannot eat the script text this process may itself be
            # executing (the remote runs `bash -s` off a pipe). PATH is
            # snapshotted and restored because sha256sum resolves through it
            # and a sourced file may overwrite it. A file that cannot be
            # sourced yields the literal UNSOURCED — not 12 hex characters,
            # so it surfaces as a mismatch rather than as agreement.
            fp="$(env -i PATH="$PATH" bash -c '
                p="$PATH"
                set -a
                . "$1" >/dev/null 2>&1 || { printf "UNSOURCED"; exit 0; }
                set +a
                PATH="$p"
                printf %s "${!2}" | sha256sum | cut -c1-12
            ' _ "$f" "$name" </dev/null 2>/dev/null)" || true
            printf '%s|%s|%s\n' "${f##*/}" "$name" "$fp"
        done < <(grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' "$f" | tr -d = || true)
    done
}

# --- remote worker mode ---------------------------------------------------------
# Reached only via the self-pipe below (`bash -s -- --scan`), never a user
# argument: the main path treats every argument as a host. Scans the REMOTE's
# own $HOME/.config/keys with no directory knob — deliberately, so a forwarded
# variable can never steer one machine's scan at another machine's keystore.
if [ "${1:-}" = "--scan" ]; then
    scan_keystore "$HOME/.config/keys" || {
        echo "keys-diff: cannot read the keystore at $HOME/.config/keys" >&2
        exit 3
    }
    exit 0
fi

[ $# -eq 1 ] || { echo "usage: scripts/keys-diff.sh <host>" >&2; exit 2; }
host="$1"

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# --- local side -----------------------------------------------------------------
# A keystore we cannot read is a could-not-look, not agreement.
scan_keystore "$KEYS_DIFF_LOCAL_DIR" > "$work/local.records" || {
    echo "keys-diff: cannot read the local keystore at $KEYS_DIFF_LOCAL_DIR" >&2
    exit 2
}

# --- remote side: this same file, the host's own keystore ------------------------
# Any ssh or remote-scan failure is loud and exits 2, never reported as
# agreement. A real unreachable host is ssh exit 255; the remote worker exits
# 3 when its own keystore is unreadable. Both arrive here as a non-zero rc.
ssh_rc=0
$KEYS_DIFF_SSH "$host" bash -s -- --scan < "$SCRIPT_PATH" \
    > "$work/remote.records" 2> "$work/remote.err" || ssh_rc=$?
if [ "$ssh_rc" -ne 0 ]; then
    echo "keys-diff: could not inspect the keystore on $host (remote scan exited $ssh_rc)" >&2
    cat "$work/remote.err" >&2
    exit 2
fi

# --- comparison -----------------------------------------------------------------
# Records into `file|name`-keyed maps, then per-file: files on one machine
# only, names on one side only, fingerprint mismatches, and one agree line
# per compared file that diverged nowhere.
declare -A L R
while IFS='|' read -r lf ln lfp; do
    [ -n "$lf" ] || continue
    L["$lf|$ln"]="$lfp"
done < "$work/local.records"
while IFS='|' read -r rf rn rfp; do
    [ -n "$rf" ] || continue
    R["$rf|$rn"]="$rfp"
done < "$work/remote.records"

cut -d'|' -f1 "$work/local.records"  | sort -u > "$work/lfiles"
cut -d'|' -f1 "$work/remote.records" | sort -u > "$work/rfiles"

divergence=0
declare -A diverged

# Files present on one machine only. Their names also surface one by one in
# the name comparison below; the file-level line is the line a human greps
# for. `while` runs on redirection, not in a pipe, so `divergence=1` reaches
# this shell.
while IFS= read -r f; do
    printf '%s exists only locally (missing remotely)\n' "$f"
    divergence=1
done < <(comm -23 "$work/lfiles" "$work/rfiles")
while IFS= read -r f; do
    printf '%s exists only remotely (missing locally)\n' "$f"
    divergence=1
done < <(comm -13 "$work/lfiles" "$work/rfiles")

# Names and fingerprints, over the sorted union of `file|name` keys. The
# mismatch line format is fixed: `file name fingerprint mismatch local=<fp>
# remote=<fp>` — fingerprints only, never a value.
while IFS= read -r key; do
    [ -n "$key" ] || continue
    f="${key%%|*}"
    n="${key#*|}"
    if [ -n "${L[$key]+x}" ] && [ -z "${R[$key]+x}" ]; then
        printf '%s %s defined only locally\n' "$f" "$n"
        divergence=1; diverged["$f"]=1
    elif [ -z "${L[$key]+x}" ] && [ -n "${R[$key]+x}" ]; then
        printf '%s %s defined only remotely\n' "$f" "$n"
        divergence=1; diverged["$f"]=1
    elif [ "${L[$key]}" != "${R[$key]}" ]; then
        printf '%s %s fingerprint mismatch local=%s remote=%s\n' \
            "$f" "$n" "${L[$key]}" "${R[$key]}"
        divergence=1; diverged["$f"]=1
    fi
done < <({ printf '%s\n' "${!L[@]}"; printf '%s\n' "${!R[@]}"; } | sort -u)

# One agree line per file compared on both sides that diverged nowhere. A
# file named here with no mismatch, no one-side name and no missing side is
# the only all-clear this script ever prints — and it is printed only after
# both sides were actually read.
while IFS= read -r f; do
    [ -n "${diverged[$f]+x}" ] && continue
    printf 'agree: %s\n' "$f"
done < <(comm -12 "$work/lfiles" "$work/rfiles")

exit "$divergence"
