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
#   - `for pid in $(pgrep -f foo); do echo $pid; done` enumerates, never polls:
#     no sleep, so it passes even though `for` is a loop keyword.
#   - `pgrep -af waiter` on its own investigates: no loop, no sleep, passes.
#   - `until [ -f /tmp/ready ]; do sleep 5; done` polls a file, not a process:
#     no pgrep, passes. Out of scope on purpose — this guard owns one class.
#   - `kill -0 "$PID"` in a loop is the CORRECT form this message recommends,
#     and must never be blocked: no pgrep, passes.
#
# Requiring `sleep` is what makes it safe to grep for a bare word: a command
# that merely *mentions* pgrep while looping over something else — a sweep
# written to hunt these very waiters — does not sleep, and is not blocked. That
# case is not hypothetical; it fired against an earlier draft of this guard.
#
# WHAT THIS GUARD DOES NOT CATCH, all deliberate, none of them observed in the
# 105 measured instances (every one of which was an inline Bash command):
#
#   - **Write-then-execute.** The hook matches PreToolUse(Bash) only, so a
#     waiter written into a script file by the Write tool and then run as
#     `./helper.sh` is never scanned. This is the real hole, and it is
#     architectural rather than a regex gap: nothing here sees a file's
#     contents. Closing it would need a second hook on Write, matching the same
#     shapes against file bodies — worth doing only if the class shows up.
#   - **A different predicate.** `ps aux | grep foo` or a bare busy-wait with no
#     sleep polls just as badly. Naming pgrep alone in a deny message would
#     advertise the substitution, which is why the message below leads with the
#     general shape and mentions pgrep second.
#   - **A heredoc.** Commands carrying `<<WORD` are skipped wholesale, because
#     writing text ABOUT this defect is indistinguishable, to a grep, from
#     running it — and the text most often written about it is this repo's own
#     memory note, which quotes the banned shape verbatim. The cost is that
#     `bash <<EOF … EOF` would slip through. Documentation authoring is
#     frequent; that shape has never been seen.
#
# Residual false positives, known and accepted rather than fixed, because
# narrowing further costs more complexity than the misfire costs a caller:
# a command whose *search patterns* happen to contain all three words
# (`grep -RIn pgrep . | grep -E "sleep|until"`) is blocked. Split it in two, or
# search with the Grep tool. A backgrounded monitor
# (`while true; do pgrep -c nginx; sleep 30; done &`) is ALSO blocked, and that
# one is not a misfire: it strands exactly like a waiter, by design.

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
# A heredoc means the command is writing text, not running a loop. See above.
echo "$cmd" | grep -qP '<<-?\s*[\x27"]?\w' && exit 0

echo "$cmd" | grep -qP '\bpgrep\b'             || exit 0
echo "$cmd" | grep -qP '\bsleep\b'             || exit 0
echo "$cmd" | grep -qP '\b(until|while|for)\b' || exit 0

echo "BLOCKED: this waits for a process by polling it in a shell loop. Any such predicate matches the waiting shell's own command line — pgrep is only the usual one — so the loop waits for itself, and it outlives the session reparented to init. Swapping the predicate does not fix it. Launch the job with run_in_background and let the completion notification arrive. If something truly must be polled, wait on a PID captured beforehand (until ! kill -0 \"\$PID\" 2>/dev/null) or on a marker the job writes when it ends — never on a pattern that can describe itself." >&2
exit 2
