#!/bin/bash
set -euo pipefail
# PreToolUse hook: block a mutating git/erg command when the cwd CLAIMS a harness
# worktree (`.../.claude/worktrees/<name>/`) but `git rev-parse --show-toplevel`
# resolves somewhere else — the live worktree-identity preflight (ticket 0296).
#
# Incident I1 (aedist, 2026-06-11/12): a session's worktree was deregistered
# mid-session; the directory lingered, so bare git fell through to the PRIMARY
# repo and a `git checkout -B` moved the primary checkout off main. Every
# existing guard checks only the weak predicate ("cwd is *some* worktree"); this
# one re-derives ownership per command — does rev-parse still match the name the
# cwd claims — on the hot path. Overhead: one rev-parse (~5-20 ms), and only
# after two pure-string fast-paths reject the common case.
#
# Exit 0 = allow, exit 2 = block with a stderr message.
#
# Fail-CLOSED when jq is missing (contrast guard-cd-primary-repo.sh, which is a
# narrow advisory and fails open): this guard protects the primary-checkout
# integrity invariant, so a missing parser must block, not wave a mutation
# through unchecked.

input=$(cat)

if ! command -v jq &>/dev/null; then
    echo "BLOCKED: jq not found — guard-worktree-identity.sh cannot parse tool input." >&2
    exit 2
fi

cmd=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
[ -z "$cmd" ] && exit 0

cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
[ -z "$cwd" ] && exit 0  # fail-safe: cannot tell which tree this session owns

# Fast path 1 (pure string, no subprocess): cwd not under a harness worktree →
# primary-checkout work is governed by other guards.
case "$cwd" in
    */.claude/worktrees/*) ;;
    *) exit 0 ;;
esac

# Fast path 2 (pure string, no git call yet): command carries no mutating verb →
# read-only git (status/log/diff) and everything else pass untouched.
# erg's install/update/init also mutate on-disk state (skills/molt calls
# `erg update` to replace the installed binary), so they are gated too.
echo "$cmd" | grep -qP '\bgit\s+(commit|checkout|switch|merge|rebase|push|reset|add|mv|rm|stash)\b' \
  || echo "$cmd" | grep -qP '\berg\s+(new|close|log|label|unlabel|archive|rm|migrate|init|install|update)\b' \
  || exit 0

# Whitelist: an explicit `git -C <path>` names its target tree, so the cwd
# identity is irrelevant — that idiom is the sanctioned way to mutate another
# tree on purpose (rules/git.md).
if echo "$cmd" | grep -qP '\bgit\s+-C\s'; then
    exit 0
fi

# cwd = .../.claude/worktrees/<name>/...  →  extract <name> and the primary root.
worktree_rest="${cwd#*/.claude/worktrees/}"
worktree_name="${worktree_rest%%/*}"
primary_root="${cwd%%/.claude/worktrees/*}"

# The only git call: resolve the real toplevel FROM THE CWD explicitly (-C),
# never the ambient shell cwd. Empty = cwd was deleted / not in a repo →
# fail-safe allow (nothing to compare against; other guards cover the rest).
toplevel=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
[ -z "$toplevel" ] && exit 0

# Identity mismatch: the tree git resolves is not the worktree the cwd claims,
# or it is the primary root itself (the I1 fall-through). Block.
if [ "$(basename "$toplevel")" != "$worktree_name" ] || [ "$toplevel" = "$primary_root" ]; then
    echo "BLOCKED: worktree identity mismatch. cwd claims worktree '$worktree_name' but git resolves to '$toplevel'." >&2
    echo "This is the I1 fall-through: a deregistered/moved worktree lets bare git mutate the wrong tree (e.g. the primary checkout)." >&2
    echo "Re-enter the correct worktree, or for intentional cross-tree work name the target explicitly: git -C <path> ..." >&2
    exit 2
fi

exit 0
