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

# Normalize away shell quote characters before matching. A quoted verb token
# (`git "commit"`) otherwise breaks the git↔verb adjacency the regex relies on
# and slips through. Stripping quotes also splits a semicolon/ampersand that was
# hiding inside a quoted argument into its own segment below, which only makes
# the guard MORE conservative (it errs toward the identity check, never away).
# Two indirections stay opaque to any static command-string scan and are OUT OF
# SCOPE here: command substitution (`git $(echo commit)`) and git aliases
# (`git ci` for commit) — a regex cannot see through either without invoking git
# itself. See ticket 0302 if closing the alias gap ever becomes necessary.
#
# Known residual FALSE-POSITIVE gap (ticket 0354, accepted, not fixed): a
# mutating verb token that appears as literal text INSIDE a quoted argument of a
# read-only command is misread as a mutation. `grep 'erg close' f`, `echo 'git
# commit later'` both match ERG_MUT/GIT_MUT. Quote-stripping here then lets the
# `tr ';&|'` split below cut a grep pattern like `'a|erg close|b'` into a bare
# `erg close` segment. Consequence is bounded and fail-SAFE: it only ever
# over-blocks, never mis-allows, and in a HEALTHY worktree it does not even
# block (the identity check passes; cost is one skipped fast-path). It bites
# only under a real identity mismatch (husk / deregistered worktree) AND when
# the read-only command's args literally contain a git/erg verb. Workaround:
# name the tree with `git -C`, or run from a non-worktree cwd. A robust fix
# (quote-aware split + verb anchored to command position) is deferred in 0354.
norm=${cmd//\"/}
norm=${norm//\'/}

# Mutating-verb patterns, reused by the fast path and the per-segment scan.
# The git list adds the destructive verbs the original allowlist missed
# (cherry-pick/revert/apply/am/restore/filter-branch/gc/pull/clean, worktree
# remove|move|prune|add, branch|tag with a delete/force/move short flag, config,
# fetch --prune). Dual-mode verbs (branch/tag) are gated only in their
# destructive flag form so read-only listing (`git branch -vv`) still passes.
# Long-form flags (`git branch --delete`) are a known residual gap.
GIT_MUT='\bgit\s+(commit|checkout|switch|merge|rebase|push|reset|add|mv|rm|stash|cherry-pick|revert|apply|am|restore|filter-branch|gc|pull|clean|worktree\s+(remove|move|prune|add)|(branch|tag)\s+-[a-zA-Z]*[dDfFmM]|config|fetch\s+--prune)\b'
ERG_MUT='\berg\s+(new|close|log|label|unlabel|archive|rm|migrate|init|install|update)\b'

# Fast path 2 (pure string, no git call yet): command carries no mutating verb →
# read-only git (status/log/diff) and everything else pass untouched.
# erg's install/update/init also mutate on-disk state (skills/molt calls
# `erg update` to replace the installed binary), so they are gated too.
echo "$norm" | grep -qP "$GIT_MUT" \
  || echo "$norm" | grep -qP "$ERG_MUT" \
  || exit 0

# Whitelist, re-checked PER SEGMENT (ticket 0302 reroll). An explicit
# `git -C <path>` names its target tree, so the cwd identity is irrelevant —
# the sanctioned cross-tree idiom (rules/git.md). But the exemption is sound
# ONLY for the segment that carries the -C: a compound like
# `git -C X status && git commit -m y` must NOT let the leading `git -C` whitelist
# its trailing BARE `git commit`, which mutates whatever bare git resolves to.
# The old guard tested the literal substring `git -C ` over the WHOLE command and
# waved the entire chain through — the I1 fall-through this guard exists to close.
# Fix: split on shell separators (&&, ||, ;, |, &) and require every MUTATING
# segment to name -C in ITSELF; any mutating segment without its own -C forces
# the identity check below. (Note: printf adds a trailing newline so `read`
# does not drop the final, separator-less segment.)
needs_check=0
while IFS= read -r seg; do
    if echo "$seg" | grep -qP "$GIT_MUT"; then
        if echo "$seg" | grep -qP '\bgit\s+-C\s'; then
            continue
        fi
        needs_check=1
        break
    fi
    if echo "$seg" | grep -qP "$ERG_MUT"; then
        needs_check=1
        break
    fi
done < <(printf '%s\n' "$norm" | tr ';&|' '\n')
[ "$needs_check" -eq 0 ] && exit 0

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
