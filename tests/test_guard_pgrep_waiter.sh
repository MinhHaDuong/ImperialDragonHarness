#!/usr/bin/env bash
# Tests for scripts/guard-pgrep-waiter.sh — the PreToolUse Bash hook that blocks
# a shell loop polling for a process with pgrep (exit 2 = deny, 0 = allow).
#
# The guard is driven entirely by the JSON payload on stdin, which is also how
# the runtime invokes it, so every case here spawns the real script and feeds it
# real payloads. Nothing is sourced or mocked.
#
# The block that matters is "must ALLOW". A guard is easy to make correct by
# denying everything, and this one greps for a bare word: `pgrep` appears in
# every command written to *investigate* these waiters. Each allow case below is
# a command someone actually needs to run — one of them fired against an earlier
# draft of this guard, in this session, while hunting the waiters it blocks.
set -euo pipefail
export LC_ALL=C

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-pgrep-waiter.sh"
fail=0
# Cases actually executed, asserted against EXPECTED at the end. A mangled case
# — a backtick in a description firing command substitution, say — otherwise
# skips silently and the suite still prints PASS. That happened while this file
# was being written, which is the same all-clear-indistinguishable-from-could-
# not-look defect the guard itself exists to prevent.
ran=0
EXPECTED=18

# Feed a command through the hook, return its exit code.
probe() {
    printf '%s' "$1" \
        | jq -R '{tool_input: {command: .}}' \
        | "$HOOK" 2>/dev/null
}

deny() {  # $1 = description, $2 = command
    ran=$((ran + 1))
    local rc=0
    probe "$2" || rc=$?
    if [ "$rc" -ne 2 ]; then
        echo "FAIL (should DENY, got exit $rc): $1"
        echo "      $2"
        fail=$((fail + 1))
    fi
}

allow() {  # $1 = description, $2 = command
    ran=$((ran + 1))
    local rc=0
    probe "$2" || rc=$?
    if [ "$rc" -ne 0 ]; then
        echo "FAIL (should ALLOW, got exit $rc): $1"
        echo "      $2"
        fail=$((fail + 1))
    fi
}

# --- must DENY: the measured shapes -----------------------------------------
# Taken verbatim from session transcripts, including the two workarounds an
# agent invented after meeting the self-match — those are the strongest cases,
# since an agent writing them has already been bitten once.
deny "the canonical waiter" \
    'until [ -z "$(pgrep -f '\''make check'\'' 2>/dev/null)" ]; do sleep 25; done'
deny "eval-wrapped, as the stranded 14h57 specimen was" \
    'eval '\''until [ -z "$(pgrep -f make check)" ]; do sleep 25; done'\''; echo FINI'
deny "workaround: tolerate one match (itself)" \
    'until [ "$(pgrep -c -f '\''make check'\'')" -le 1 ]; do sleep 20; done'
deny "workaround: double negation" \
    'until [ ! -z "$(pgrep -f denials.py)" ] && false || [ -z "$(pgrep -f denials.py)" ]; do sleep 5; done'
deny "while form" \
    'while pgrep -f build.sh >/dev/null; do sleep 10; done'
deny "loop split across lines" \
    'until [ -z "$(pgrep -f make)" ]
do
  sleep 30
done'
deny "bounded for-loop poll — the reviewer's find, one token to close" \
    'for i in $(seq 1 100); do pgrep -f make || break; sleep 5; done'
# Not a misfire: a backgrounded monitor strands exactly like a waiter, by
# design, and reparents the same way. Blocking it is the intended behaviour.
deny "backgrounded monitor loop" \
    'while true; do pgrep -c nginx; sleep 30; done &'

# --- must ALLOW: everything a person or agent legitimately needs -------------
allow "enumeration, not polling" \
    'for pid in $(pgrep -f waiter); do echo "$pid"; done'
allow "bare investigation" \
    'pgrep -af "make check"'
allow "the CORRECT form this guard recommends — never block it" \
    'until ! kill -0 "$PID" 2>/dev/null; do sleep 10; done'
allow "polling a marker file, no process predicate" \
    'until grep -qE "passed|failed" "$OUT"; do sleep 15; done'
allow "a sweep that MENTIONS the word until while looping over pgrep output" \
    'for pid in $(pgrep -u "$USER" -f "until" 2>/dev/null); do readlink /proc/$pid/cwd; done'
allow "loop with sleep, no process predicate at all" \
    'until [ -f /tmp/ready ]; do sleep 5; done'
allow "pgrep and sleep, but no loop" \
    'pgrep -f make; sleep 2; echo done'
allow "enumeration survives for becoming a loop keyword: sleep is what saves it" \
    'for pid in $(pgrep -f x); do readlink /proc/$pid/cwd; done'
# Writing text ABOUT this defect is indistinguishable, to a grep, from running
# it — and the text most often written about it is this repo's own memory note,
# which quotes the banned shape verbatim. A heredoc edit to that note must not
# trip the guard that the note documents.
allow "heredoc that documents the banned shape" \
    'cat >> note.md <<EOF
until [ -z "$(pgrep -f make)" ]; do sleep 25; done
EOF'
allow "empty command" ''

# --- must DENY: the probe cannot parse its input ----------------------------
# An all-clear indistinguishable from "I could not look" is not a guard, so a
# missing jq denies rather than passing everything through.
# A bare PATH=/nonexistent is the wrong probe: the script dies at its first
# external command (exit 127) without ever reaching the jq test, and 127 is not
# 2 — the test would fail for a reason unrelated to what it claims to check.
# Give it a PATH that has everything it needs EXCEPT jq.
NOJQ=$(mktemp -d)
trap 'rm -r "$NOJQ"' EXIT
for bin in cat grep; do ln -s "$(command -v "$bin")" "$NOJQ/$bin"; done
rc=0
printf '{"tool_input":{"command":"echo hi"}}' | env PATH="$NOJQ" "$HOOK" >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 2 ]; then
    echo "FAIL (should DENY when jq is absent, got exit $rc)"
    fail=$((fail + 1))
fi
# Control on the control: the same PATH must still let a normal run reach the
# jq check, or the case above proves nothing about jq.
if [ ! -x "$NOJQ/cat" ] || command -v jq >/dev/null && [ -e "$NOJQ/jq" ]; then
    echo "FAIL: the no-jq fixture is malformed"
    fail=$((fail + 1))
fi

if [ "$ran" -ne "$EXPECTED" ]; then
    echo "FAIL: ran $ran cases, expected $EXPECTED — a case was mangled or lost"
    fail=$((fail + 1))
fi

if [ "$fail" -eq 0 ]; then
    echo "PASS: guard-pgrep-waiter.sh"
else
    echo "$fail failure(s)"
    exit 1
fi
