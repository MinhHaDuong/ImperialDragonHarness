#!/usr/bin/env bash
# Tests for scripts/guard-commit-on-main.sh — the PreToolUse hook that
# blocks git commit when on the main/master branch (exit 2 = deny, exit 0 = allow).
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-commit-on-main.sh"
fail=0

# Create a temp git repo so `git branch --show-current` behaves predictably.
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR" "${PRIMARY2:-}"' EXIT

git -C "$TMPDIR" init -q
git -C "$TMPDIR" config user.email "test@example.com"
git -C "$TMPDIR" config user.name "Test"
# Create an initial commit so HEAD exists and branch name resolves.
git -C "$TMPDIR" commit --allow-empty -q -m "init"
# Rename the default branch to main (handles repos where default is 'master').
git -C "$TMPDIR" branch -m main 2>/dev/null || true

# Run the hook from inside $TMPDIR, or an explicit cwd (2nd arg). When an
# explicit cwd is passed, the payload also carries a `.cwd` field (like the
# sibling guard-cd-primary-repo tests) — reuses the jq payload-construction
# pattern from tests/test_guard_cd_primary_repo.sh:20-28. Omitting the 2nd
# arg preserves the plain (no `.cwd`) payload shape used by the original
# main/master/feature-branch assertions below.
_run() {
    local cmd="$1" cwd="${2:-$TMPDIR}"
    local payload
    if [[ -n "${2:-}" ]]; then
        payload=$(printf '{"tool_name":"Bash","tool_input":{"command":%s},"cwd":%s}' \
            "$(printf '%s' "$cmd" | jq -Rs .)" \
            "$(printf '%s' "$cwd" | jq -Rs .)")
    else
        payload=$(printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
            "$(printf '%s' "$cmd" | jq -Rs .)")
    fi
    printf '%s' "$payload" | (cd "$cwd" && bash "$HOOK" >/dev/null 2>&1)
    echo $?
}

_assert_blocked() {
    local label="$1" cmd="$2" cwd="${3:-}"
    local rc; rc=$(_run "$cmd" "$cwd")
    if [[ "$rc" == "2" ]]; then
        echo "PASS: blocks $label"
    else
        echo "FAIL: expected block (exit 2) for $label; got exit $rc — cmd: $cmd"
        fail=1
    fi
}

_assert_allowed() {
    local label="$1" cmd="$2" cwd="${3:-}"
    local rc; rc=$(_run "$cmd" "$cwd")
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

# --- I1 fall-through: primary checkout moved off main, tree identity check --
# Simulate incident I1: a stray `git checkout -B feature` moves the PRIMARY
# checkout off main. A PLAIN (unregistered) directory under .claude/worktrees/
# makes git's toplevel walk-up land back on the primary repo. Because the
# branch is 'feature' (not main), the old branch-only guard passed the commit
# WRONGLY; the fix blocks on tree identity. The fall-through is organic — it
# comes from git's rev-parse walk-up, not from a hardcoded path match.
PRIMARY2=$(mktemp -d)
git -C "$PRIMARY2" init -q
git -C "$PRIMARY2" config user.email "test@example.com"
git -C "$PRIMARY2" config user.name "Test"
git -C "$PRIMARY2" commit --allow-empty -q -m "init"
git -C "$PRIMARY2" branch -m main 2>/dev/null || true
git -C "$PRIMARY2" checkout -B feature -q          # I1: primary now off main
PLAINWT="$PRIMARY2/.claude/worktrees/t001"
mkdir -p "$PLAINWT"                                 # NOT a `git worktree add`
_assert_blocked "git commit on primary via plain worktree dir (I1)" \
                "git commit -m x" "$PLAINWT"

# --- bare primary root off main: tree-identity check must fire (0297) ------
# Round-1 gate finding: the tree-identity check must block even when `.cwd` is
# the PRIMARY checkout root addressed directly — no `.claude/worktrees/` marker
# segment in the path. This is the exact scenario from the ticket's Context: a
# stray `git checkout -B` moves the primary off main; the commit must be blocked
# regardless of branch name, not just when the cwd is dressed as a worktree path.
_assert_blocked "git commit on bare primary root off main (0297)" \
                "git commit -m x" "$PRIMARY2"

# --- positive: a real registered worktree on a feature branch → allowed ----
# `git worktree add` gives the dir its own toplevel, distinct from the primary
# root, so the tree-identity check passes through and layer-2 (branch=feature)
# allows the commit. No false positive on legitimate worktree commits.
REALWT="$PRIMARY2/.claude/worktrees/t002"
git -C "$PRIMARY2" worktree add -q -b feature-wt "$REALWT"
_assert_allowed "git commit in real registered worktree on feature branch" \
                "git commit -m x" "$REALWT"

if (( fail )); then
    exit 1
fi
echo "PASS: guard-commit-on-main blocks commits on main/master and allows everything else"
