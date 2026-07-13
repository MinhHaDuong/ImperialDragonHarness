#!/usr/bin/env bash
# Tests for scripts/guard-worktree-identity.sh — the PreToolUse Bash hook that
# blocks a mutating git/erg command when the cwd claims a harness worktree
# (`.../.claude/worktrees/<name>/`) but `git rev-parse --show-toplevel` resolves
# elsewhere (exit 2 = deny, exit 0 = allow). See ticket 0296 / incident I1:
# a deregistered worktree whose directory lingers, so bare git falls through to
# the PRIMARY repo and mutates the wrong tree.
#
# The guard is driven purely via the JSON payload's .cwd (worktree detection +
# the -C target for rev-parse) and .tool_input.command. Fixtures are REAL git
# repos — rev-parse is never mocked, so the test exercises the actual walk-up.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-worktree-identity.sh"
fail=0

# --- real git fixtures ----------------------------------------------------
FIX=$(mktemp -d)
trap 'rm -rf "$FIX"' EXIT

PRIMARY="$FIX/primary"
mkdir -p "$PRIMARY"
git -C "$PRIMARY" init -q
git -C "$PRIMARY" config user.email t@e.st
git -C "$PRIMARY" config user.name tester
git -C "$PRIMARY" commit -q --allow-empty -m init

# Case (a) fixture: a PLAIN directory under .claude/worktrees/ — NOT a
# registered worktree. rev-parse from here walks up to $PRIMARY.
BROKEN="$PRIMARY/.claude/worktrees/t001"
mkdir -p "$BROKEN"

# Case (b) fixture: a REAL registered worktree at the same layout shape.
GOOD="$PRIMARY/.claude/worktrees/t002"
git -C "$PRIMARY" worktree add -q -b wt002 "$GOOD"

# Feed a Bash tool-input payload (with cwd) to the hook; print "<rc>\t<stderr>".
_run() {
    local cmd="$1" cwd="$2"
    local err rc
    err=$(printf '{"tool_name":"Bash","tool_input":{"command":%s},"cwd":%s}' \
            "$(printf '%s' "$cmd" | jq -Rs .)" \
            "$(printf '%s' "$cwd" | jq -Rs .)" \
            | bash "$HOOK" 2>&1 1>/dev/null) && rc=0 || rc=$?
    printf '%s\t%s' "$rc" "$err"
}

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

# --- (a) I1 replay: mutating git in a deregistered worktree → BLOCK --------
_assert_blocked "I1 git commit in deregistered worktree" \
                "git commit -m x" "$BROKEN"
_assert_blocked "I1 git checkout -B off main" \
                "git checkout -B main" "$BROKEN"
_assert_blocked "I1 erg close in deregistered worktree" \
                "erg close 123 done" "$BROKEN"

# --- (b) false-positive path: real registered worktree → ALLOW -------------
_assert_allowed "mutating git in a real registered worktree" \
                "git commit -m x" "$GOOD"
_assert_allowed "erg new in a real registered worktree" \
                "erg new 'a title'" "$GOOD"

# --- (c) explicit git -C anywhere → ALLOW regardless of cwd ----------------
_assert_allowed "git -C whitelist in the broken worktree" \
                "git -C $PRIMARY commit -m x" "$BROKEN"

# --- (d) read-only git in the broken worktree → ALLOW (verb fast-path) -----
_assert_allowed "git status in the broken worktree" "git status" "$BROKEN"
_assert_allowed "git log in the broken worktree"    "git log -1"  "$BROKEN"
_assert_allowed "git diff in the broken worktree"   "git diff"    "$BROKEN"

# --- fast path: cwd not a harness worktree → ALLOW ------------------------
_assert_allowed "mutating git in the primary root (not a worktree)" \
                "git commit -m x" "$PRIMARY"

# --- fail-safe: cwd deleted (rev-parse empty) → ALLOW ---------------------
GONE="$PRIMARY/.claude/worktrees/t999-deleted"
_assert_allowed "cwd does not exist (rev-parse empty) → fail-safe allow" \
                "git commit -m x" "$GONE"

# --- payload without .cwd → fail-safe allow -------------------------------
rc=$(printf '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"}}' \
        | bash "$HOOK" >/dev/null 2>&1; echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no .cwd (fail-safe)"
else
    echo "FAIL: expected allow for payload with no .cwd; got exit $rc"
    fail=1
fi

# --- jq missing → FAIL-CLOSED (exit 2): this guard protects primary-checkout
# integrity, so a missing parser must block, not wave through. ---------------
_tmpbin=$(mktemp -d)
ln -s "$(type -P cat)" "$_tmpbin/cat"
_real_bash="$(type -P bash)"
rc=$(printf '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"},"cwd":"%s"}' "$BROKEN" \
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
echo "PASS: guard-worktree-identity blocks mutations when cwd worktree identity mismatches git"
