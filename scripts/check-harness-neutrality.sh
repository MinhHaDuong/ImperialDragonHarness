#!/usr/bin/env bash
# Check that new commits to skills/ and tickets/ don't encode consumer-project assumptions.
# Runs diff-only against BASE (default: origin/main).
# Exit 0 = clean. Exit 1 = leakage found.
# Suppress a match by placing <!-- harness-extension-point --> on the preceding line.
#
# Special case: BASE=HEAD uses git diff --cached (staged changes, for pre-commit hook).

set -euo pipefail

BASE="${1:-origin/main}"

# Consumer-project patterns to reject
PATTERNS=(
    'Climate[-_]finance'
    'AEDIST'
    'CIRED\.digital'
)

# Build combined regex
combined=$(printf '%s\n' "${PATTERNS[@]}" | paste -sd '|' -)

fail=0

# Get the diff: added lines only, in skills/**/*.md and tickets/*.erg
if [ "$BASE" = "HEAD" ]; then
    # Pre-commit: check staged changes
    diff_output=$(git diff --cached -- 'skills/**/*.md' 'tickets/*.erg' 2>/dev/null)
else
    # CI / manual: check commits since diverging from BASE
    diff_output=$(git diff "$BASE"...HEAD -- 'skills/**/*.md' 'tickets/*.erg' 2>/dev/null || \
                  git diff "$BASE" -- 'skills/**/*.md' 'tickets/*.erg' 2>/dev/null)
fi

if [ -z "$diff_output" ]; then
    exit 0
fi

# Parse diff: track current file, check for escape hatch on preceding line
current_file=""
prev_line=""

while IFS= read -r line; do
    # Track which file we're in
    if [[ "$line" =~ ^\+\+\+\ b/(.+)$ ]]; then
        current_file="${BASH_REMATCH[1]}"
        prev_line=""
        continue
    fi
    # Only check added lines (exclude diff header +++)
    if [[ "$line" =~ ^\+[^+] ]]; then
        content="${line:1}"
        if echo "$content" | grep -qEi "$combined"; then
            # Check escape hatch in the preceding line (context or another added line)
            if echo "$prev_line" | grep -qF '<!-- harness-extension-point -->'; then
                : # suppressed
            else
                echo "LEAK: $current_file: $content"
                fail=1
            fi
        fi
    fi
    # Track previous non-diff-header line for escape hatch check
    if [[ ! "$line" =~ ^(diff\ |index\ |---\ |\+\+\+\ |@@) ]]; then
        prev_line="$line"
    fi
done <<< "$diff_output"

exit $fail
