#!/bin/bash
set -euo pipefail
# PreToolUse hook: block `cd <primary-repo-root> && <mutating git/erg>` during a
# worktree session. In an EnterWorktree session the shell already sits in the
# worktree and resets there after every command; prefixing `cd ~/<repo> &&`
# silently cd's into the PRIMARY checkout (on main), so the mutation lands on
# the wrong tree. Read-only inspection (status/log/diff) is not penalised.
# See ticket 0189. Sibling of guard-destructive-bash.sh / the worktree-path guard.
#
# Exit 0 = allow, exit 2 = block with a stderr message.
#
# Fail-OPEN (not fail-closed) when jq is missing: this is a narrow advisory
# guard against one reflex, not a security boundary — a missed warning is far
# cheaper than blocking every Bash call on a box without jq. (Contrast
# guard-destructive-bash.sh, which fails closed because it gates real data loss.)
#
# Deliberate YAGNI: only `cd && <git/erg>` is handled. We do NOT inspect
# `sed -i`, `rm`, or `>>` redirects targeting the primary repo — those are not
# the observed reflex and would broaden the hot path for little gain.

input=$(cat)

command -v jq &>/dev/null || exit 0

cmd=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
[ -z "$cmd" ] && exit 0

# Fast path: no `cd` word → nothing to guard. One grep, before the second jq.
echo "$cmd" | grep -qwP 'cd' || exit 0

cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
[ -z "$cwd" ] && exit 0  # fail-safe: cannot tell if this is a worktree session

# Worktree detection (pure string, no git calls): cwd under .claude/worktrees/.
case "$cwd" in
    */.claude/worktrees/*) ;;
    *) exit 0 ;;
esac
# primary_root = the prefix before the worktree marker.
primary_root="${cwd%%/.claude/worktrees/*}"

# Extract the first `cd <target>` token (before &&, ;, |, or whitespace end).
# Take the text after the first `cd ` and lop off at the first delimiter.
rest="${cmd#*cd }"
target="${rest%%[ ;&|]*}"
[ -z "$target" ] && exit 0

# Strip surrounding quotes and a trailing slash.
target="${target#\"}"; target="${target%\"}"
target="${target#\'}"; target="${target%\'}"
target="${target%/}"

# Expand leading `~` and a literal `$HOME` using $HOME.
target="${target/#\~/$HOME}"
target="${target//\$HOME/$HOME}"

# Normalize `..` traversal and symlinks before the equality check (ticket 0323,
# minor A): `cd $primary/sub/.. && git commit` resolves back to $primary but does
# not lexically equal it, so it would slip past the string compare below. This is
# the same evasion residual 1 closed in pretooluse-worktree-path-guard.sh.
# realpath -m collapses `..` and resolves symlinks in existing components while
# tolerating a not-yet-existing leaf. Warn on the fallback so the degraded
# (raw-path, still-vulnerable) mode is visible rather than silent.
if command -v realpath &>/dev/null; then
    target=$(realpath -m -- "$target" 2>/dev/null || echo "$target")
else
    echo "guard: realpath unavailable, path normalization skipped" >&2
fi

# Only the primary repo root itself is the offence; subtrees (incl. the
# worktree path, which lives under primary_root) are fine.
[ "$target" = "$primary_root" ] || exit 0

# Mutating git verbs or erg verbs *after* the cd → block. Scan $rest (the text
# following the first `cd`), not $cmd: a mutation *before* the cd ran in the
# worktree and is safe (e.g. `git add . && cd <primary>`), so scanning the whole
# command would false-block it — contra the ticket's fail-safe invariant.
if echo "$rest" | grep -qP '\bgit\s+(commit|add|switch|checkout|reset|merge|rebase|push|mv|rm|stash)\b' \
   || echo "$rest" | grep -qP '\berg\s+(close|archive)\b'; then
    echo "BLOCKED: 'cd $target && ...' targets the PRIMARY repo (on main), but this is a worktree session (cwd=$cwd)." >&2
    echo "The mutation would land on the wrong tree. Either:" >&2
    echo "  - drop the 'cd' — plain git/erg already operate on the worktree branch, or" >&2
    echo "  - for an intentional primary-repo op, use: git -C $primary_root ..." >&2
    exit 2
fi

exit 0
