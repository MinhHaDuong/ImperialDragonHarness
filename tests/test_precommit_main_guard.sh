#!/usr/bin/env bash
# Tests for the main-branch-guard block in hooks/pre-commit.
#
# The guard refuses a direct commit on `main` in the PRIMARY checkout, but must
# stay silent for commits made from a linked worktree (raid/agent worktrees),
# even on main — and for commits on any non-main branch. Overrides:
# ALLOW_MAIN_COMMIT=1, CI=true, or a rebase/merge in progress.
#
# Strategy: extract ONLY the main-branch-guard fragment from hooks/pre-commit
# into a fresh scratch repo's pre-commit hook (via core.hooksPath), so the
# erg/skills-catalog guards in the full hook do not interfere, then exercise
# real `git commit` invocations.
set -euo pipefail

# Neutralize ambient CI markers and any inherited override so the refusal
# cases are deterministic. The guard intentionally skips when CI / GITHUB_ACTIONS
# is set (the ticket excludes CI), and GitHub Actions runners always export
# GITHUB_ACTIONS=true — without scrubbing them here, every "should refuse"
# case would silently pass-through under CI and the suite would fail only on
# the runner, not locally. The override sub-cases re-set CI/ALLOW_MAIN_COMMIT
# inline for the one invocation that exercises them.
unset CI GITHUB_ACTIONS ALLOW_MAIN_COMMIT 2>/dev/null || true

cd "$(dirname "$0")/.."
REPO_ROOT="$PWD"
HOOK_SRC="$REPO_ROOT/hooks/pre-commit"
fail=0

# Extract the shebang + the main-branch-guard block only.
GUARD_BODY=$(awk '
    /^# --- main-branch-guard ---$/ { n++; print; next }
    n==1 { print }
    n==2 { print; exit }
' "$HOOK_SRC")

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PRIMARY="$TMPDIR/primary"
git init -q "$PRIMARY"
git -C "$PRIMARY" config user.email "test@example.com"
git -C "$PRIMARY" config user.name "Test"

# Install the extracted guard as the hook for the primary repo.
mkdir -p "$PRIMARY/.githooks"
{
    echo '#!/bin/sh'
    printf '%s\n' "$GUARD_BODY"
} > "$PRIMARY/.githooks/pre-commit"
chmod +x "$PRIMARY/.githooks/pre-commit"
git -C "$PRIMARY" config core.hooksPath "$PRIMARY/.githooks"

# Seed an initial commit (bypass the hook so we have a base), then rename to main.
git -C "$PRIMARY" commit --allow-empty -q -m "init" --no-verify
git -C "$PRIMARY" branch -m main 2>/dev/null || true

_pass() { echo "PASS: $1"; }
_fail() { echo "FAIL: $1"; fail=1; }

# --- RED: commit on main in the primary checkout is refused ---------------
echo "a" > "$PRIMARY/a.txt"; git -C "$PRIMARY" add a.txt
if git -C "$PRIMARY" commit -q -m "on main" 2>/dev/null; then
    _fail "expected refusal committing on main in primary checkout"
else
    _pass "refuses commit on main in primary checkout"
fi

# --- override ALLOW_MAIN_COMMIT=1 lets the same commit through ------------
if ALLOW_MAIN_COMMIT=1 git -C "$PRIMARY" commit -q -m "on main (override)" 2>/dev/null; then
    _pass "ALLOW_MAIN_COMMIT=1 permits commit on main"
else
    _fail "ALLOW_MAIN_COMMIT=1 should permit commit on main"
fi

# --- override CI=true lets the commit through ----------------------------
echo "b" > "$PRIMARY/b.txt"; git -C "$PRIMARY" add b.txt
if CI=true git -C "$PRIMARY" commit -q -m "on main (CI)" 2>/dev/null; then
    _pass "CI=true permits commit on main"
else
    _fail "CI=true should permit commit on main"
fi

# --- GREEN: commit on a feature branch is allowed ------------------------
git -C "$PRIMARY" switch -c feature/x -q
echo "c" > "$PRIMARY/c.txt"; git -C "$PRIMARY" add c.txt
if git -C "$PRIMARY" commit -q -m "on branch" 2>/dev/null; then
    _pass "allows commit on a feature branch"
else
    _fail "expected commit on a feature branch to be allowed"
fi
git -C "$PRIMARY" switch -q main

# --- GREEN: commit on main from a LINKED WORKTREE is allowed -------------
# This is the core discriminator: a worktree's toplevel != primary toplevel.
WT="$TMPDIR/wt"
git -C "$PRIMARY" worktree add -q "$WT" -b wt-main 2>/dev/null
# Force the worktree onto main as well, to prove the branch name alone does not
# trigger the guard — only branch==main AND primary_root==this_root does.
git -C "$WT" branch -f wt-on-main main >/dev/null 2>&1 || true
# Recreate the worktree checked out on a branch literally named main is not
# possible (main is checked out in primary); instead verify the guard stays
# silent for a worktree even when its branch resolves to main's tip. Simplest
# faithful check: commit from the worktree on its own branch must pass, AND a
# worktree whose HEAD symref is main must also pass. We simulate the latter by
# pointing the worktree HEAD at main directly.
echo "d" > "$WT/d.txt"; git -C "$WT" add d.txt
git -C "$WT" symbolic-ref HEAD refs/heads/main
if git -C "$WT" commit -q -m "on main from worktree" 2>/dev/null; then
    _pass "allows commit on main from a linked worktree (guard stays silent)"
else
    _fail "guard must stay silent for a commit on main from a linked worktree"
fi

# --- rebase-in-progress simulation: guard must not block -----------------
git -C "$PRIMARY" switch -q main
GIT_DIR=$(git -C "$PRIMARY" rev-parse --git-dir)
mkdir -p "$PRIMARY/$GIT_DIR/rebase-merge"
echo "e" > "$PRIMARY/e.txt"; git -C "$PRIMARY" add e.txt
if git -C "$PRIMARY" commit -q -m "during rebase" 2>/dev/null; then
    _pass "allows commit on main while a rebase is in progress"
else
    _fail "guard must not block commits during an in-progress rebase"
fi
rm -rf "$PRIMARY/$GIT_DIR/rebase-merge"

if (( fail )); then
    exit 1
fi
echo "PASS: pre-commit main-branch-guard refuses primary-main commits and stays silent for worktrees/branches/overrides"
