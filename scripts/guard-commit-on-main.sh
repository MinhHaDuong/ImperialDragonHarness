#!/bin/bash
set -euo pipefail
# PreToolUse hook: block git commit on main/master branch.
# Enforces the "main is read-only" rule from git.md.

input=$(cat)

if ! command -v jq &>/dev/null; then
    echo "BLOCKED: jq not found — guard-commit-on-main.sh cannot parse tool input." >&2
    exit 2
fi

cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# Only check git commit commands
echo "$cmd" | grep -qP '\bgit\s+commit\b' || exit 0

# Layer 1 — tree identity. Branch name is a proxy; the material predicate is
# "this commit lands on the PRIMARY checkout". Incident I1 defeated the
# branch-only check: a stray `git checkout -B` moved the primary off main, and
# the guard then allowed commits on it. Consume `.cwd` from the hook JSON (the
# same idiom as scripts/guard-cd-primary-repo.sh:21-40) and block when the cwd
# resolves to the primary checkout, whatever the branch.
#
# Derive "primary root" from git plumbing, not from a path-string pattern:
# `--git-common-dir` points at the shared .git of the primary checkout, so its
# parent IS the primary root — for a bare primary cwd AND for any worktree,
# registered or not. When the cwd's own toplevel equals that primary root, the
# commit lands on the primary. A registered worktree has its own distinct
# toplevel, so it falls through to layer 2. This is the same technique as
# scripts/pretooluse-worktree-path-guard.sh:24-26 and needs no `.claude/worktrees`
# naming convention — the earlier case-gated version silently no-op'd when the
# primary was addressed as a bare root path (ticket 0297, round-1 gate finding).
cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -n "$cwd" ]; then
    toplevel=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
    git_common_dir=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    if [ -n "$toplevel" ] && [ -n "$git_common_dir" ]; then
        primary_root=$(dirname "$git_common_dir")
        if [ "$toplevel" = "$primary_root" ]; then
            echo "BLOCKED: cwd '$cwd' resolves to the PRIMARY checkout ($primary_root) — a bare primary root, or an unregistered/deregistered worktree that falls through to it. Committing here lands on the primary, whatever the branch. Create/enter a real worktree first." >&2
            exit 2
        fi
    fi
fi

# Layer 2 — branch name. Use `git -C "$cwd"` when cwd is known; bare git
# otherwise (preserves today's behaviour for payloads that carry no `.cwd`,
# where layer 1 is silently skipped — a residual gap for cwd-less callers).
if [ -n "$cwd" ]; then
    branch=$(git -C "$cwd" branch --show-current 2>/dev/null || true)
else
    branch=$(git branch --show-current 2>/dev/null || true)
fi

if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
    echo "BLOCKED: committing directly to $branch. Create a branch first: git switch -c <branch-name>" >&2
    exit 2
fi

exit 0
