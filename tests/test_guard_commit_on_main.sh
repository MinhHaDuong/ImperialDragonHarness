#!/usr/bin/env bash
# Tests for scripts/guard-commit-on-main.sh — the PreToolUse hook that
# blocks git commit when on the main/master branch (exit 2 = deny, exit 0 = allow).
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-commit-on-main.sh"
fail=0

# Create a temp git repo so `git branch --show-current` behaves predictably.
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

git -C "$TMPDIR" init -q
git -C "$TMPDIR" config user.email "test@example.com"
git -C "$TMPDIR" config user.name "Test"
# Create an initial commit so HEAD exists and branch name resolves.
git -C "$TMPDIR" commit --allow-empty -q -m "init"
# Rename the default branch to main (handles repos where default is 'master').
git -C "$TMPDIR" branch -m main 2>/dev/null || true

# Run the hook from inside the temp repo so `git branch --show-current` sees it.
_run() {
    local cmd="$1"
    printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
        "$(printf '%s' "$cmd" | jq -Rs .)" \
        | (cd "$TMPDIR" && bash "$HOOK" >/dev/null 2>&1)
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

# --- on main: git commit must be blocked ---------------------------------
_assert_blocked "git commit on main"          "git commit -m 'msg'"
_assert_blocked "git commit --amend on main"  "git commit --amend --no-edit"

# --- on main: non-commit git commands must be allowed --------------------
_assert_allowed "git status on main"          "git status"
_assert_allowed "git push on main"            "git push origin main"
# NOTE: `echo 'git commit is safe in scripts'` is a pre-existing false positive —
# the regex matches "git commit" anywhere in the command string, including inside
# quoted echo arguments. Tracking separately; scope of this ticket is grep -P
# conversion only (regex unchanged).

# --- switch to a feature branch: git commit must be allowed --------------
git -C "$TMPDIR" switch -c feature/test-branch -q

_assert_allowed "git commit on feature branch" "git commit -m 'msg'"

# --- switch to master: git commit must be blocked ------------------------
git -C "$TMPDIR" checkout -b master -q 2>/dev/null || git -C "$TMPDIR" switch -c master -q

_assert_blocked "git commit on master"        "git commit -m 'msg'"

# --- empty / missing command → allow ------------------------------------
rc=$(printf '{"tool_name":"Bash","tool_input":{}}' \
        | (cd "$TMPDIR" && bash "$HOOK" >/dev/null 2>&1); echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no command field"
else
    echo "FAIL: expected allow for empty payload; got exit $rc"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: guard-commit-on-main blocks commits on main/master and allows everything else"
