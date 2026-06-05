#!/bin/bash
set -euo pipefail
# PostToolUse hook: run ruff on edited Python files.
# Feeds errors back to the agent so it can self-correct.

input=$(cat)

if ! command -v jq &>/dev/null; then
    exit 0  # non-blocking: lint is advisory, not a gate
fi

file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0
[[ "$file_path" == *.py ]] || exit 0

# Run ruff check (fix safe violations) only — deliberately NOT `ruff format`.
# The repo has no repo-wide formatter (ticket 0201, PR #275): running
# `ruff format` here silently reinstated the exact per-PR churn 0201 reverted,
# every time an agent touched a .py file via Edit/Write. Lint stays (advisory,
# self-correcting); formatting is a no-op until a formatter is adopted
# repo-wide. See ticket 0212.
if command -v uv &>/dev/null; then
    output=$(uv run ruff check --fix --quiet "$file_path" 2>&1 || true)
elif command -v ruff &>/dev/null; then
    output=$(ruff check --fix --quiet "$file_path" 2>&1 || true)
else
    exit 0  # no linter available
fi

if [ -n "$output" ]; then
    echo "ruff: $output"
fi

exit 0
