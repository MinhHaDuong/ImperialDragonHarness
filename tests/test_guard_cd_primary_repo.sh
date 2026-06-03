#!/usr/bin/env bash
# Tests for scripts/guard-cd-primary-repo.sh — the PreToolUse Bash hook that
# blocks `cd <primary-repo-root> && <mutating git/erg>` during a worktree
# session (exit 2 = deny, exit 0 = allow). See ticket 0189.
#
# The guard is driven purely via the JSON payload's .cwd field (worktree
# detection) and .tool_input.command — no test-only backdoor in the script.
# HOME is pinned so leading-`~` expansion in the guard is deterministic.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-cd-primary-repo.sh"
fail=0

PRIMARY="/home/testuser/repo"
WORKTREE="/home/testuser/repo/.claude/worktrees/t001"

# Feed a Bash tool-input payload (with cwd) to the hook; print "<rc>\t<stderr>".
# HOME pinned so `cd ~/repo` expands to /home/testuser/repo inside the guard.
_run() {
    local cmd="$1" cwd="$2"
    local err rc
    err=$(printf '{"tool_name":"Bash","tool_input":{"command":%s},"cwd":%s}' \
            "$(printf '%s' "$cmd" | jq -Rs .)" \
            "$(printf '%s' "$cwd" | jq -Rs .)" \
            | env HOME=/home/testuser bash "$HOOK" 2>&1 1>/dev/null) && rc=0 || rc=$?
    printf '%s\t%s' "$rc" "$err"
}

# Exit code only (stderr discarded).
_rc() {
    local out; out=$(_run "$1" "$2")
    printf '%s' "${out%%$'\t'*}"
}

_assert_blocked() {
    local label="$1" cmd="$2" cwd="$3"
    local rc; rc=$(_rc "$cmd" "$cwd")
    if [[ "$rc" == "2" ]]; then
        echo "PASS: blocks $label"
    else
        echo "FAIL: expected block (exit 2) for $label; got exit $rc — cmd: $cmd"
        fail=1
    fi
}

_assert_allowed() {
    local label="$1" cmd="$2" cwd="$3"
    local rc; rc=$(_rc "$cmd" "$cwd")
    if [[ "$rc" == "0" ]]; then
        echo "PASS: allows $label"
    else
        echo "FAIL: expected allow (exit 0) for $label; got exit $rc — cmd: $cmd"
        fail=1
    fi
}

# Allowed AND must emit nothing on stderr (the "must be SILENT" cases).
_assert_allowed_silent() {
    local label="$1" cmd="$2" cwd="$3"
    local out rc err
    out=$(_run "$cmd" "$cwd")
    rc="${out%%$'\t'*}"
    err="${out#*$'\t'}"
    if [[ "$rc" == "0" && -z "$err" ]]; then
        echo "PASS: allows + silent $label"
    else
        echo "FAIL: expected allow (exit 0) + empty stderr for $label; got exit $rc, stderr: '$err' — cmd: $cmd"
        fail=1
    fi
}

# --- BLOCK: cd into PRIMARY then a mutating verb, during a worktree session ---
_assert_blocked "cd PRIMARY && git commit"     "cd $PRIMARY && git commit -m x"          "$WORKTREE"
_assert_blocked "cd PRIMARY && git add -A"      "cd $PRIMARY && git add -A"               "$WORKTREE"
_assert_blocked "cd PRIMARY && git switch -c x" "cd $PRIMARY && git switch -c x"          "$WORKTREE"
_assert_blocked "cd PRIMARY && git reset HEAD~1" "cd $PRIMARY && git reset HEAD~1"        "$WORKTREE"
_assert_blocked "cd PRIMARY && git push origin main" "cd $PRIMARY && git push origin main" "$WORKTREE"
_assert_blocked "cd PRIMARY && erg close 123"   "cd $PRIMARY && erg close 123"            "$WORKTREE"
_assert_blocked "cd ~/repo && git commit (tilde)" "cd ~/repo && git commit -m x"          "$WORKTREE"

# --- ALLOW ----------------------------------------------------------------
# Same cd+commit but cwd is the primary repo itself (not a worktree session).
_assert_allowed "cd PRIMARY && git commit, cwd=PRIMARY (no worktree)" \
                "cd $PRIMARY && git commit -m x" "$PRIMARY"
# Bare mutating command inside the worktree — already targets the worktree.
_assert_allowed "bare git commit in worktree" "git commit -m x" "$WORKTREE"
# cd that stays inside the worktree tree.
_assert_allowed "cd into worktree subtree && git commit" \
                "cd $WORKTREE && git commit -m x" "$WORKTREE"
# cd into an unrelated dir.
_assert_allowed "cd /tmp && git commit" "cd /tmp && git commit -m x" "$WORKTREE"
# Empty command.
_assert_allowed "empty command" "" "$WORKTREE"

# Read-only cd into PRIMARY must be allowed AND silent (no stderr noise).
_assert_allowed_silent "cd PRIMARY && git status" "cd $PRIMARY && git status" "$WORKTREE"
_assert_allowed_silent "cd PRIMARY && git log"    "cd $PRIMARY && git log -1"  "$WORKTREE"

# --- Payload without .cwd → fail-safe allow -------------------------------
rc=$(printf '{"tool_name":"Bash","tool_input":{"command":"cd /home/testuser/repo && git commit -m x"}}' \
        | env HOME=/home/testuser bash "$HOOK" >/dev/null 2>&1; echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no .cwd (fail-safe)"
else
    echo "FAIL: expected allow for payload with no .cwd; got exit $rc"
    fail=1
fi

# --- jq missing → fail-open (narrow-scope guard) --------------------------
_tmpbin=$(mktemp -d)
ln -s "$(type -P cat)" "$_tmpbin/cat"
ln -s "$(type -P grep)" "$_tmpbin/grep"
_real_bash="$(type -P bash)"
rc=$(printf '{"tool_name":"Bash","tool_input":{"command":"cd /home/testuser/repo && git commit -m x"},"cwd":"/home/testuser/repo/.claude/worktrees/t001"}' \
        | env PATH="$_tmpbin" HOME=/home/testuser "$_real_bash" "$HOOK" >/dev/null 2>&1; echo $?)
rm -rf "$_tmpbin"
if [[ "$rc" == "0" ]]; then
    echo "PASS: fails open (exit 0) when jq is missing"
else
    echo "FAIL: expected fail-open (exit 0) without jq; got exit $rc"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: guard-cd-primary-repo blocks cd-to-primary mutations in worktree sessions"
