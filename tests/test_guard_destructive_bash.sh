#!/usr/bin/env bash
# Tests for scripts/guard-destructive-bash.sh — the PreToolUse hook that
# blocks destructive Bash commands (exit 2 = deny, exit 0 = allow).
#
# Follows the catch-the-violation / pass-clean / no-false-positive pattern
# used by the guard self-tests in .github/workflows/CI.yml, but pins the
# behaviour as a committed regression suite rather than inline CI steps.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-destructive-bash.sh"
fail=0

# Feed a Bash tool-input payload to the hook; capture exit code (never abort).
_run() {
    local cmd="$1"
    printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
        "$(printf '%s' "$cmd" | jq -Rs .)" \
        | bash "$HOOK" >/dev/null 2>&1
    echo $?
}

# A command that MUST be blocked (exit 2).
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

# A command that MUST be allowed (exit 0).
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

# --- destructive commands must be blocked ---------------------------------
_assert_blocked "rm -rf"                  "rm -rf /tmp/somedir"
_assert_blocked "rm -fr (flag reorder)"   "rm -fr build"
_assert_blocked "rm --force"              "rm --force important.txt"
_assert_blocked "git reset --hard"        "git reset --hard HEAD~3"
_assert_blocked "git push --force"        "git push --force origin main"
_assert_blocked "git push -f"             "git push -f origin main"
_assert_blocked "git clean -fd"           "git clean -fd"
_assert_blocked "sudo rm"                 "sudo rm /etc/hosts"
_assert_blocked "DROP TABLE"              "psql -c 'DROP TABLE users'"
_assert_blocked "drop database (case)"    "mysql -e 'drop database prod'"

# --- safe / look-alike commands must be allowed ---------------------------
_assert_allowed "plain rm"                "rm stale.log"
_assert_allowed "rm -r without force"     "rm -r build/cache"
_assert_allowed "rm -i interactive"       "rm -i notes.txt"
_assert_allowed "git push --force-with-lease" "git push --force-with-lease origin feature"
_assert_allowed "git clean dry-run"       "git clean -n"
_assert_allowed "git reset (soft, no --hard)" "git reset HEAD~1"
_assert_allowed "ls listing"              "ls -la /var/log"
_assert_allowed "rm substring in word"    "echo performance && touch warm.txt"

# --- empty / missing command → allow (nothing to inspect) -----------------
rc=$(printf '{"tool_name":"Bash","tool_input":{}}' | bash "$HOOK" >/dev/null 2>&1; echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no command field"
else
    echo "FAIL: expected allow for empty payload; got exit $rc"
    fail=1
fi

# --- fail-closed when jq is unavailable -----------------------------------
# Build a minimal PATH that has the binaries the hook needs (cat, grep) but
# deliberately NOT jq, so `command -v jq` fails inside the hook. It must deny
# (exit 2) rather than silently allow everything. Emptying PATH entirely would
# break `cat` first (exit 127) and never reach the jq check.
# type -P resolves the real binary, ignoring any shell function/alias shims.
# env is given an absolute bash path because the restricted PATH won't find it.
_tmpbin=$(mktemp -d)
ln -s "$(type -P cat)" "$_tmpbin/cat"
ln -s "$(type -P grep)" "$_tmpbin/grep"
_real_bash="$(type -P bash)"
rc=$(printf '{"tool_name":"Bash","tool_input":{"command":"echo hi"}}' \
        | env PATH="$_tmpbin" "$_real_bash" "$HOOK" >/dev/null 2>&1; echo $?)
rm -rf "$_tmpbin"
if [[ "$rc" == "2" ]]; then
    echo "PASS: fails closed (exit 2) when jq is missing"
else
    echo "FAIL: expected fail-closed (exit 2) without jq; got exit $rc"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: guard-destructive-bash blocks destructive commands and allows safe ones"
