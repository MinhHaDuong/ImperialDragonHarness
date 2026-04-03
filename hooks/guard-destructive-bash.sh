#!/bin/bash
# PreToolUse hook: block destructive Bash commands.
# Exit 0 = allow, Exit 2 = deny with message.

# Read tool input from stdin (JSON with tool_input.command)
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# Patterns that are destructive and hard to reverse
if echo "$cmd" | grep -qE '(rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
    echo "BLOCKED: rm -rf detected. Use targeted rm or move to trash instead." >&2
    exit 2
fi

if echo "$cmd" | grep -qE '\bgit\s+reset\s+--hard\b'; then
    echo "BLOCKED: git reset --hard destroys uncommitted work. Use git stash or git checkout <file> instead." >&2
    exit 2
fi

if echo "$cmd" | grep -qE '\bgit\s+push\s+.*--force\b|\bgit\s+push\s+-f\b'; then
    echo "BLOCKED: force push can destroy remote history. Use --force-with-lease if needed." >&2
    exit 2
fi

if echo "$cmd" | grep -qE '\bgit\s+clean\s+-[a-zA-Z]*f'; then
    echo "BLOCKED: git clean -f permanently deletes untracked files. Use git clean -n to preview first." >&2
    exit 2
fi

if echo "$cmd" | grep -qE '\bsudo\s+rm\b'; then
    echo "BLOCKED: sudo rm is too dangerous for automated execution. Run manually if needed." >&2
    exit 2
fi

if echo "$cmd" | grep -qE '\bdrop\s+(table|database)\b' -i; then
    echo "BLOCKED: DROP TABLE/DATABASE detected. Run manually if intended." >&2
    exit 2
fi

exit 0
