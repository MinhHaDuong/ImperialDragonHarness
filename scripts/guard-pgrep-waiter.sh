#!/bin/bash
set -euo pipefail
# PreToolUse hook: block a shell loop that polls for a process with pgrep.
# Exit 0 = allow, Exit 2 = deny with message.
#
# The defect: `until [ -z "$(pgrep -f 'make check')" ]; do sleep 25; done` never
# terminates. The waiting shell's own command line contains the pattern, so
# pgrep matches it and the loop waits for itself. It then outlives the session,
# reparented to init, polling forever with nothing to sweep it. Written 105
# times in 101 days of transcripts, every one by an agent — including several
# that had already met the self-match and were working around it
# (`pgrep -c … -le 1`), which is the tell that the defect is the shape.
#
# The match is a THREE-WAY conjunction — loop keyword, pgrep, sleep — and each
# term is there to keep a legitimate command out:
#
#   - `for pid in $(pgrep -f foo); do …; done`  enumerates, never polls: no
#     `until`/`while`, so it passes.
#   - `pgrep -af waiter` on its own investigates: no loop, no sleep, passes.
#   - `until [ -z "$(ls /tmp/x)" ]; do sleep 5; done` polls a file, not a
#     process: no pgrep, passes. Out of scope on purpose — this guard owns one
#     defect class.
#   - `kill -0 "$PID"` in a loop is the CORRECT form this message recommends,
#     and must never be blocked: no pgrep, passes.
#
# Requiring `sleep` is what makes it safe to grep for a bare word: a command
# that merely *mentions* pgrep while looping over something else — a sweep
# written to hunt these very waiters — does not sleep, and is not blocked. That
# case is not hypothetical; it fired against an earlier draft of this guard.

input=$(cat)

# Require jq — if missing, deny by default rather than silently allowing all.
# A guard whose all-clear is indistinguishable from "I could not look" is not a
# guard.
if ! command -v jq &>/dev/null; then
    echo "BLOCKED: jq not found — guard-pgrep-waiter.sh cannot parse tool input." >&2
    exit 2
fi

cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# grep -P (PCRE): \b is spec-defined there, unlike POSIX ERE where it is a
# GNU-only extension that degrades to a literal on other builds.
echo "$cmd" | grep -qP '\bpgrep\b'        || exit 0
echo "$cmd" | grep -qP '\bsleep\b'        || exit 0
echo "$cmd" | grep -qP '\b(until|while)\b' || exit 0

echo "BLOCKED: this polls for a process in a shell loop, and a pgrep predicate matches the waiting shell's own command line — the loop waits for itself, then outlives the session. Launch the job with run_in_background and let the completion notification arrive. If something truly must be polled, wait on a PID captured beforehand (until ! kill -0 \"\$PID\" 2>/dev/null) or on a marker the job writes when it ends — never on a pattern that can describe itself." >&2
exit 2
