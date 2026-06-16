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
#
# `--unfixable F401,I001,UP` disarms a whole class of "swordfight" trap: an
# autofix that MUTATES the file between two of the agent's Edits, leaving the
# agent's pending `old_string`s stale. The three confirmed members (empirically
# reproduced, ticket-evidenced across 19 historical sessions):
#   F401 — agent adds `import X` in Edit 1, its first usage in Edit 2; the hook
#          fires in between and DELETES the still-unused import → Edit 2 NameErrors.
#   I001 — the hook REORDERS the import block; a later Edit whose `old_string`
#          spans import lines no longer matches → Edit fails.
#   UP   — pyupgrade rewrites in-body (`List[str]`→`list[str]`, `Optional[x]`→
#          `x | None`, `.format`→f-string); a later Edit targeting that text
#          finds it already changed → Edit fails.
# All three are still REPORTED (the agent sorts imports / modernizes annotations /
# drops dead imports itself — matching the project's own style rules), so nothing
# is lost except the silent mid-sequence mutation. F841 (unused var) is NOT in the
# list: its fix is unsafe and never fires without `--unsafe-fixes`. Genuinely safe
# fixes (whitespace W291/W293, blank lines, E-class) stay on — they never desync.
if command -v uv &>/dev/null; then
    output=$(uv run ruff check --fix --unfixable F401,I001,UP --quiet "$file_path" 2>&1 || true)
elif command -v ruff &>/dev/null; then
    output=$(ruff check --fix --unfixable F401,I001,UP --quiet "$file_path" 2>&1 || true)
else
    exit 0  # no linter available
fi

if [ -n "$output" ]; then
    echo "ruff: $output"
fi

exit 0
