#!/usr/bin/env bash
# Tests for scripts/block-pr-merge-in-worktree.sh (ticket 0308).
#
# The guard blocks `gh pr merge` in ANY linked git worktree — main's ref is
# locked by the primary checkout, so `gh pr merge` hits git's
# `fatal: 'main' is already used by worktree at ...` in every linked worktree,
# not only the harness `.claude/worktrees/<name>` ones. It must therefore fire
# in a harness worktree AND in an ad-hoc worktree, stay silent in the primary
# checkout, and stay silent in a submodule (whose `.git` gitdir: file shares no
# ref-locks with the superproject — its git-dir equals its own git-common-dir).
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/block-pr-merge-in-worktree.sh"
fail=0

_rc() { # <dir> [payload] → runs the hook from <dir>, echoes its exit code
    local dir="$1" payload="${2:-{\}}"
    ( cd "$dir" && printf '%s' "$payload" | bash "$HOOK" >/dev/null 2>&1; echo $? )
}

_payload() { # <command> → a PreToolUse payload carrying that command
    python3 -c 'import json,sys; print(json.dumps({"tool_input": {"command": sys.argv[1]}}))' "$1"
}

# Fixture: primary repo, a harness worktree, and an ad-hoc worktree that lives
# OUTSIDE .claude/worktrees/.
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

# 3. Ad-hoc worktree OUTSIDE .claude/worktrees/ → block (exit 2). `gh pr merge`
# fails the same ref-lock way here as in a harness worktree, so the fail-closed
# guard must fire (ticket 0308: the earlier identity predicate wrongly allowed
# this, a false negative).
rc=$(_rc "$primary/adhoc")
if [ "$rc" = "2" ]; then
    echo "PASS: blocks in an ad-hoc worktree outside .claude/worktrees/"
else
    echo "FAIL: expected block (2) in ad-hoc worktree, got $rc"
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

# 5. A submodule → allow (exit 0). A submodule's git-dir equals its own
# git-common-dir, so it is not a linked worktree and shares no ref-lock with
# the superproject; `gh pr merge` there targets the submodule's own main.
super=$(mktemp -d)
sub=$(mktemp -d)
git -C "$sub" init -q
git -C "$sub" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init-sub
git -C "$super" init -q
git -C "$super" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init-super
git -C "$super" -c protocol.file.allow=always -c user.email=t@t -c user.name=t \
    submodule add -q "$sub" mod 2>/dev/null
rc=$(_rc "$super/mod")
if [ "$rc" = "0" ]; then
    echo "PASS: allows in a submodule working tree"
else
    echo "FAIL: expected allow (0) in submodule, got $rc"
    fail=1
fi
rm -rf "$super" "$sub"

# 6. A real `gh pr merge` in a harness worktree → block (exit 2). The positive
# control: cases 1-5 pass an empty payload, so on their own they cannot tell a
# guard that reads the command from one that never looks.
rc=$(_rc "$primary/.claude/worktrees/t001" "$(_payload 'gh pr merge 449 --merge')")
if [ "$rc" = "2" ]; then
    echo "PASS: blocks a real gh pr merge in a worktree"
else
    echo "FAIL: expected block (2) for gh pr merge, got $rc"
    fail=1
fi

# 7. Ordinary work in a harness worktree → allow (exit 0). The `if:` matcher in
# settings.json hands this guard any command it cannot decompose, so a command
# substitution reaches here and must pass (2026-09-08: `erg log` was refused
# with a message about `gh pr merge`).
rc=$(_rc "$primary/.claude/worktrees/t001" "$(_payload 'erg log 0029 "$(cat note.txt)" tickets/')")
if [ "$rc" = "0" ]; then
    echo "PASS: allows an unrelated command in a worktree"
else
    echo "FAIL: expected allow (0) for an unrelated command, got $rc"
    fail=1
fi

# 8. A command naming a merge that is not gh's → allow. `git merge` is not the
# hazard: it is the documented recovery when force-push is denied.
rc=$(_rc "$primary/.claude/worktrees/t001" "$(_payload 'git merge origin/main')")
if [ "$rc" = "0" ]; then
    echo "PASS: allows git merge in a worktree"
else
    echo "FAIL: expected allow (0) for git merge, got $rc"
    fail=1
fi

git -C "$primary" worktree remove --force "$primary/.claude/worktrees/t001" 2>/dev/null || true
git -C "$primary" worktree remove --force "$primary/adhoc" 2>/dev/null || true
rm -rf "$primary"

exit $fail
