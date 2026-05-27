#!/bin/bash
set -euo pipefail
# PreToolUse hook: block "git worktree remove" when the target worktree has
# uncommitted WIP — git worktree remove --force would silently destroy it.
# Forces salvage first. Exit 0 = allow, Exit 2 = deny.
# Matcher in settings.json scopes this to "git worktree remove" commands.
# See ticket 0168.

input=$(cat)

command -v jq &>/dev/null || exit 0
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# Only act on git worktree remove (also catches it inside a compound command).
echo "$cmd" | grep -qE '\bgit[[:space:]]+worktree[[:space:]]+remove\b' || exit 0

# Extract the worktree path: first non-flag token after "remove".
after=${cmd#*worktree*remove}
read -ra toks <<< "$after"
path=""
for t in "${toks[@]}"; do
    case "$t" in
        --|--force|-f) continue ;;
        -*) continue ;;
        *) path="$t"; break ;;
    esac
done

[ -z "$path" ] && exit 0
[ -d "$path" ] || exit 0

if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
    cat >&2 <<EOF
Blocked: '$path' has uncommitted WIP — git worktree remove would destroy it.
Salvage first (commits + pushes the branch so the work survives):

  ~/.claude/scripts/worktree-salvage.sh "$path"

Then re-run the remove. See ticket 0168.
EOF
    exit 2
fi

exit 0
