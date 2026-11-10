#!/bin/bash
# Status line: model name, reasoning effort, and the context length in tokens.
# Context length is the whole prompt of the last API call: input, cache read and
# cache creation tokens summed. No usage in the input prints "?", never 0.
set -euo pipefail

input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')
TOKENS=$(echo "$input" | jq -r '.context_window.current_usage
  | if type == "object"
    then (.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)
    else empty end')

if [ -z "$TOKENS" ]; then
  SHOWN="?"
elif [ "$TOKENS" -lt 1000 ]; then
  SHOWN="$TOKENS"
elif [ "$TOKENS" -lt 10000 ]; then
  SHOWN="$((TOKENS / 1000)).$((TOKENS % 1000 / 100))K"
else
  SHOWN="$(((TOKENS + 500) / 1000))K"
fi

LABEL="$MODEL"
[ -n "$EFFORT" ] && LABEL="$LABEL/$EFFORT"

echo "[$LABEL] prompt $SHOWN"
