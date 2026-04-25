#!/bin/bash
# PreToolUse hook: block git push in automated sessions.
# Used by night-sweep and any other unattended claude run.
set -euo pipefail

input=$(cat)
command -v jq &>/dev/null || { echo "BLOCKED: jq not found — guard-no-push.sh cannot parse tool input." >&2; exit 2; }

cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

if echo "$cmd" | grep -qE '\bgit\s+push\b'; then
    echo "BLOCKED (night-sweep): git push is not allowed in automated mode. Commits are local — a human will push." >&2
    exit 2
fi

exit 0
