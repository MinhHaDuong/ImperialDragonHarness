#!/bin/bash
# SessionEnd hook: remove THIS session's scratch directories (ticket 0854).
#
# Every session gets `<temp-root>/<cwd-key>/<session-id>/{scratchpad,tasks}`,
# one per distinct cwd it visits, and the runtime only ever creates them —
# there is no delete-on-exit, no startup sweep, and no settings key. Where the
# temp root is a tmpfs under a per-user quota, the leftovers of finished
# sessions are charged to every later session of the same user until the Bash
# tool dies with EDQUOT. This hook covers every normal exit.
#
# Ownership is clean by construction: the only directories removed are the ones
# whose basename equals the session id in this hook's own JSON payload. No
# liveness test is needed and none is performed — the session being ended IS
# the owner, and its own processes would read as live. Nothing else is ever
# touched, which is what keeps the "never delete a live session's directory"
# invariant: a sibling session's id never matches. Orphans left by a crash or a
# kill are the sweep's job (`session_scratch.py --sweep`, run from molt), which
# does apply a liveness test.
#
# The temp root is NOT relocated here. The runtime's own relocation knob is an
# operator decision — it must also stay short, because sandbox socket paths are
# built under it — so the harness reports usage and cleans up after itself
# rather than moving the root.
#
# The invariant is that this hook NEVER exits non-zero: a failing SessionEnd
# hook is noise on every session teardown, and there is nothing a caller could
# do with the status. `set -e` alone would break that — any failing probe aborts
# before the final `exit 0` — so the EXIT trap pins the status while `-e` still
# stops the script the moment something unexpected happens. Every command below
# is additionally guarded (`|| true`, or an `if`), and no bare
# `[ … ] && …` is used at top level: under `-e` a false test there would abort
# the script, which with this trap would look exactly like a clean no-op.
set -euo pipefail
trap 'exit 0' EXIT

# Read the payload first, whatever we do with it: exiting before draining stdin
# would hand the runtime an EPIPE on a hook that is supposed to be invisible.
payload=$(cat 2>/dev/null) || payload=""

# A subagent shares the PARENT session's scratch directory — measured on this
# host 2026-09-07: a subagent's environment carries the parent's session id, and
# its scratchpad path is the parent's directory. If a child context ever fires
# SessionEnd, honouring it would delete a live session's scratchpad out from
# under it. Child contexts clean up nothing; the parent's own exit does it.
if [ -n "${CLAUDE_CODE_CHILD_SESSION:-}" ]; then
    exit 0
fi

session_id=""
if command -v jq >/dev/null 2>&1; then
    session_id=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null) \
        || session_id=""
fi
if [ -z "$session_id" ]; then
    # jq is not guaranteed on a fresh machine; the payload is one flat object,
    # so a literal-field extraction is enough for the fallback.
    session_id=$(printf '%s' "$payload" | tr -d '\n' \
        | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
        | head -1) || session_id=""
fi
if [ -z "$session_id" ]; then exit 0; fi

# The id becomes a path component, so it must be a plain name: no separator, no
# `.`, no glob metacharacter. `*` or `..` here would widen the deletion from one
# session to the whole temp root — every live session on the machine.
case "$session_id" in
    *[!A-Za-z0-9_-]*) exit 0 ;;
esac
if [ "${#session_id}" -lt 8 ]; then exit 0; fi

# Test seam, and the operator's relocation knob if one is set. The uid suffix is
# the runtime's own layout: one root per user under the temp base.
root="${CLAUDE_SESSION_SCRATCH_ROOT:-}"
if [ -z "$root" ]; then
    base="${CLAUDE_CODE_TMPDIR:-${TMPDIR:-/tmp}}"
    root="${base%/}/claude-$(id -u 2>/dev/null || echo "${UID:-0}")"
fi
# A symlinked root is refused outright: `-d` reports through the link, so
# `<root> -> <victim>` would make every removal below land in the victim's real
# tree. The root has to be a real directory of ours or there is nothing to do.
if [ -L "$root" ] || [ ! -d "$root" ]; then exit 0; fi

shopt -s nullglob
for key_dir in "$root"/*/; do
    # The glob's trailing slash makes a symlinked cwd key match too, and its
    # target is a real directory that can live anywhere: check the key itself
    # before building a path under it, or the deletion escapes the root
    # entirely. Same guard as the Python sibling's `key_dir.is_symlink()`.
    if [ -L "${key_dir%/}" ]; then continue; fi
    target="${key_dir}${session_id}"
    # A symlink reports -d through its target: refuse to follow one out of the
    # root. Only a real directory is ever removed.
    if [ -L "$target" ] || [ ! -d "$target" ]; then continue; fi
    rm -rf -- "$target" 2>/dev/null || true
    # Prune the cwd-key directory once its last session is gone; a key still
    # holding another session's directory is left alone (rmdir refuses).
    rmdir -- "${key_dir%/}" 2>/dev/null || true
done

exit 0
