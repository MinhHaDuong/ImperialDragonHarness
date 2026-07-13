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
# worktree path resolves back to the primary root, whatever the branch.
cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -n "$cwd" ]; then
    case "$cwd" in
        */.claude/worktrees/*)
            # primary_root = the prefix before the worktree marker.
            primary_root="${cwd%%/.claude/worktrees/*}"
            toplevel=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
            if [ -n "$toplevel" ] && [ "$toplevel" = "$primary_root" ]; then
                echo "BLOCKED: cwd '$cwd' looks like a worktree but git resolves it to the PRIMARY checkout ($primary_root) — an unregistered/deregistered worktree falls through to the primary tree. Committing here lands on the primary. Create/enter a real worktree first." >&2
                exit 2
            fi
            ;;
    esac
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
