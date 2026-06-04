#!/usr/bin/env bash
# Shell tests for the /reviewers skill dispatcher.
# Verifies stub behaviour with an empty panel roster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEWERS="${SCRIPT_DIR}/reviewers.sh"
PASS=0
FAIL=0

assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "PASS: $label"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $label"
        echo "  expected: $(printf '%q' "$expected")"
        echo "  actual:   $(printf '%q' "$actual")"
        FAIL=$((FAIL + 1))
    fi
}

assert_exit_0() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "PASS: $label"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $label (exit code $?)"
        FAIL=$((FAIL + 1))
    fi
}

# --- list with empty roster ---
out=$("$REVIEWERS" list)
assert_eq "list: empty roster prints 'no reviewers configured'" \
    "no reviewers configured" "$out"

# --- request with empty roster ---
out=$("$REVIEWERS" request 42)
assert_eq "request: empty roster prints 'no reviewers configured'" \
    "no reviewers configured" "$out"

# --- request exits 0 with empty roster ---
assert_exit_0 "request: exits 0 with empty roster" \
    "$REVIEWERS" request 42

# --- harvest with empty roster produces no output ---
out=$("$REVIEWERS" harvest 42)
assert_eq "harvest: empty roster produces empty output" \
    "" "$out"

# --- harvest exits 0 ---
assert_exit_0 "harvest: exits 0 with empty roster" \
    "$REVIEWERS" harvest 42

# --- scorecard is callable ---
assert_exit_0 "scorecard: exits 0 (smoke)" \
    "$REVIEWERS" scorecard 42 "PASS — 0 blocking"

# --- scorecard prints stub message ---
out=$("$REVIEWERS" scorecard 42 "PASS — 0 blocking")
assert_eq "scorecard: stub message mentions MR" \
    "scorecard: stub — would log verdict for MR #42: PASS — 0 blocking" "$out"

# --- request without arg fails ---
if "$REVIEWERS" request 2>/dev/null; then
    echo "FAIL: request: missing arg should fail"
    FAIL=$((FAIL + 1))
else
    echo "PASS: request: missing arg fails"
    PASS=$((PASS + 1))
fi

# --- Summary ---
echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
