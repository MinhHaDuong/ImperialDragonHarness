#!/usr/bin/env bash
# Capture one memory journal entry under the project's memory/journal/YYYY/,
# applying the encrypted-in-repo audience policy (author decision 2026-10-02,
# PR #1112; pinned here for ticket 0988 — the policy named age and
# ~/.config/keys but not the command, the key filename or the per-project
# key selection).
#
# Usage: memory-capture.sh <repo-dir> <audience> <slug>   (entry text on stdin)
#   repo-dir   the project repository, or a worktree of it
#   audience   public  — cleared for the repository's public audience:
#                        written as plaintext Markdown
#              private — not cleared: encrypted as age ciphertext, plaintext
#                        never written anywhere in the working tree
#   slug       filename slug for the dated entry (letters, digits, ., _, -)
#
# The audience judgment happens at capture, before the first byte is written:
# the capturing agent decides public vs not-cleared, and this helper
# mechanically enforces the consequence. It writes the entry and nothing else —
# committing belongs to the caller (roar's single wrap-up bundle), which keeps
# memory out of the pulled checkout and off uncommitted state (ticket 0988).
#
# Pinned commands:
#   new key:    age-keygen -o <key>
#   recipient:  age-keygen -y <key>
#   encrypt:    age -r <recipient> -o <entry>.age        (plaintext on stdin)
#   decrypt:    age -d -i <key> <entry>.age
#
# Key selection — one age X25519 identity per project at
#   ~/.config/keys/memory/<sha256(normalized origin URL)[:16]>.age
# derived at capture time from the repository's own origin remote: scheme,
# user and .git suffix stripped, lowercased (so https and ssh clones of the
# same project share one key). Repository content names this derivation
# mechanism, never a key file; computing the filename aids no decryption (the
# ciphertext-at-rest limit is recorded in docs/memory-v8/pilot.md). The key is
# created with age-keygen on first private capture, mode 600, never tracked.
set -euo pipefail

die() { echo "memory-capture: $*" >&2; exit 1; }

usage() {
    echo "usage: memory-capture.sh <repo-dir> <public|private> <slug>   (entry text on stdin)" >&2
    exit 2
}

# The per-project key path: sha256[:16] of the normalized origin URL, under
# ~/.config/keys/memory/. Normalization strips scheme and user, converts the
# scp-like git@host:path form, drops a .git suffix and lowercases, so every
# transport of the same project derives one key. Created on first use.
project_key() {
    local repo=$1 url norm keydir
    url=$(git -C "$repo" remote get-url origin 2>/dev/null) \
        || die "private capture needs an origin remote to derive the project key"
    norm=$(printf '%s' "$url" \
        | sed -e 's|^\([a-z+]*://\)git@||' -e 's|^[a-z+]*://||' \
              -e 's|^\([^/]*\)@||' -e 's|^git@||' \
              -e 's|:\([^/]\)|/\1|' -e 's|\.git$||' \
              | tr '[:upper:]' '[:lower:]')
    keydir=$HOME/.config/keys/memory
    mkdir -p "$keydir"
    key="$keydir/$(printf '%s' "$norm" | sha256sum | cut -c1-16).age"
    if [ ! -f "$key" ]; then
        (umask 077 && age-keygen -o "$key" >/dev/null) \
            || die "could not create the project key at $key"
        chmod 600 "$key"
    fi
    printf '%s' "$key"
}


[ $# -eq 3 ] || usage
dir=$1 audience=$2 slug=$3

case "$audience" in
    public|private) ;;
    *) die "audience must be public or private, got '$audience'" ;;
esac
case "$slug" in
    ''|.|..) die "empty slug" ;;
    *[!A-Za-z0-9._-]*) die "slug may only use letters, digits, dot, underscore, dash: '$slug'" ;;
esac

repo=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || die "not a git repository: $dir"

date=$(date +%Y-%m-%d)
year=$(date +%Y)
entry="memory/journal/$year/$date-$slug"
[ "$audience" = public ] && suffix=md || suffix=age
path="$repo/$entry.$suffix"
[ ! -e "$path" ] || die "refusing to overwrite an existing entry: $entry.$suffix (journal is append-only; corrections are new entries)"
mkdir -p "$repo/memory/journal/$year"

if [ "$audience" = public ]; then
    # Plaintext is the cleared audience: straight to the journal.
    cat > "$path" || { rm -f "$path"; die "could not write $entry.$suffix"; }
else
    # Not cleared: stdin pipes straight into age; no plaintext file, no
    # tempfile, exists anywhere under the repository.
    key=$(project_key "$repo") || die "could not derive the project key"
    recipient=$(age-keygen -y "$key" 2>/dev/null) || die "could not read the recipient from $key"
    if ! age -r "$recipient" -o "$path"; then
        rm -f "$path"
        die "could not encrypt the entry to $entry.$suffix (nothing written)"
    fi
    chmod 0644 "$path"
fi

echo "memory-capture: $entry.$suffix ($audience)"
