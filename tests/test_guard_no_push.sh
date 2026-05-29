#!/usr/bin/env bash
# Tests for scripts/guard-no-push.sh — the PreToolUse hook that
# blocks git push in automated sessions (exit 2 = deny, exit 0 = allow).
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-no-push.sh"
fail=0

# Feed a Bash tool-input payload to the hook; capture exit code (never abort).
_run() {
    local cmd="$1"
    printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
        "$(printf '%s' "$cmd" | jq -Rs .)" \
        | bash "$HOOK" >/dev/null 2>&1
    echo $?
}

# Variant with BEAT_HOUSEKEEPING_PR and BEAT_HOUSEKEEPING_BRANCH set.
_run_with_env() {
    local cmd="$1" branch="$2"
    printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
        "$(printf '%s' "$cmd" | jq -Rs .)" \
        | env BEAT_HOUSEKEEPING_PR=1 BEAT_HOUSEKEEPING_BRANCH="$branch" \
          bash "$HOOK" >/dev/null 2>&1
    echo $?
}

_assert_blocked() {
    local label="$1" cmd="$2"
    local rc; rc=$(_run "$cmd")
    if [[ "$rc" == "2" ]]; then
        echo "PASS: blocks $label"
    else
        echo "FAIL: expected block (exit 2) for $label; got exit $rc — cmd: $cmd"
        fail=1
    fi
}

_assert_allowed() {
    local label="$1" cmd="$2"
    local rc; rc=$(_run "$cmd")
    if [[ "$rc" == "0" ]]; then
        echo "PASS: allows $label"
    else
        echo "FAIL: expected allow (exit 0) for $label; got exit $rc — cmd: $cmd"
        fail=1
    fi
}

# --- git push must be blocked ---------------------------------------------
_assert_blocked "git push"                    "git push origin main"
_assert_blocked "git push --force"            "git push --force origin main"
_assert_blocked "git push -u"                 "git push -u origin feature"

# --- non-push git commands must be allowed --------------------------------
_assert_allowed "git commit"                  "git commit -m 'msg'"
_assert_allowed "git status"                  "git status"
# NOTE: `echo 'git push is blocked'` is a pre-existing false positive — the
# regex matches "git push" anywhere in the command string, including inside
# quoted echo arguments. Tracking separately; scope of this ticket is grep -P
# conversion only (regex unchanged).

# --- empty / missing command → allow -------------------------------------
rc=$(printf '{"tool_name":"Bash","tool_input":{}}' | bash "$HOOK" >/dev/null 2>&1; echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no command field"
else
    echo "FAIL: expected allow for empty payload; got exit $rc"
    fail=1
fi

# --- housekeeping exception: matching branch → allow --------------------
rc=$(_run_with_env "git push origin claude/housekeeping-20260529" "claude/housekeeping-20260529")
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows push when housekeeping exception matches branch"
else
    echo "FAIL: expected allow for housekeeping push; got exit $rc"
    fail=1
fi

# --- housekeeping exception: wrong branch → still blocked ----------------
rc=$(_run_with_env "git push origin main" "claude/housekeeping-20260529")
if [[ "$rc" == "2" ]]; then
    echo "PASS: blocks push to main even with housekeeping env set"
else
    echo "FAIL: expected block when pushing wrong branch; got exit $rc"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: guard-no-push blocks git push and allows everything else"
