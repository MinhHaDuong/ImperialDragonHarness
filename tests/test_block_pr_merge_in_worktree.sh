#!/usr/bin/env bash
# Tests for scripts/block-pr-merge-in-worktree.sh (ticket 0308).
#
# The guard blocks `gh pr merge` inside a git worktree (main is locked by the
# parent). It must fire in a harness worktree (.claude/worktrees/<name>) and
# stay silent in the primary checkout and in trees that merely carry a
# `.git` gitdir: file but are not harness worktrees (submodules, ad-hoc
# worktrees) — the false positive the weak `[ -f .git ]` predicate produced.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/block-pr-merge-in-worktree.sh"
fail=0

_rc() { # <dir> → runs the hook from <dir>, echoes its exit code
    local dir="$1"
    ( cd "$dir" && echo '{}' | bash "$HOOK" >/dev/null 2>&1; echo $? )
}

# Fixture: primary repo, a harness worktree, and an ad-hoc worktree that lives
# OUTSIDE .claude/worktrees/ (stands in for a submodule / non-harness worktree,
# both of which have a `.git` gitdir: file).
primary=$(mktemp -d)
git -C "$primary" init -q
git -C "$primary" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
mkdir -p "$primary/.claude/worktrees"
git -C "$primary" worktree add -q "$primary/.claude/worktrees/t001"
git -C "$primary" worktree add -q "$primary/adhoc"

# 1. Harness worktree → block (exit 2).
rc=$(_rc "$primary/.claude/worktrees/t001")
if [ "$rc" = "2" ]; then
    echo "PASS: blocks in a harness worktree"
else
    echo "FAIL: expected block (2) in harness worktree, got $rc"
    fail=1
fi

# 2. Primary checkout (.git is a real directory) → allow (exit 0).
rc=$(_rc "$primary")
if [ "$rc" = "0" ]; then
    echo "PASS: allows in the primary checkout"
else
    echo "FAIL: expected allow (0) in primary checkout, got $rc"
    fail=1
fi

# 3. Worktree OUTSIDE .claude/worktrees/ → allow (exit 0). Regression for
# ticket 0308: the weak `[ -f .git ]` predicate blocked ANY gitdir: file here.
rc=$(_rc "$primary/adhoc")
if [ "$rc" = "0" ]; then
    echo "PASS: allows in a worktree outside .claude/worktrees/"
else
    echo "FAIL: expected allow (0) in ad-hoc worktree, got $rc"
    fail=1
fi

# 4. A directory in no git repo at all → allow (exit 0).
tmp=$(mktemp -d)
rc=$(_rc "$tmp")
if [ "$rc" = "0" ]; then
    echo "PASS: allows outside any git repo"
else
    echo "FAIL: expected allow (0) outside any repo, got $rc"
    fail=1
fi
rm -rf "$tmp"

git -C "$primary" worktree remove --force "$primary/.claude/worktrees/t001" 2>/dev/null || true
git -C "$primary" worktree remove --force "$primary/adhoc" 2>/dev/null || true
rm -rf "$primary"

exit $fail
