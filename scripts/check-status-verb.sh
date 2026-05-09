#!/usr/bin/env bash
# Guard against legacy %erg "status <state>" verb in skill log examples.
# Valid verbs: created, closed, note. The "status" verb was removed in %erg v1.
# Usage: check-status-verb.sh [file-or-dir ...]   (default: skills/ tickets/AGENTS.md)
set -euo pipefail

if [ $# -eq 0 ]; then
    TARGETS=(skills/ tickets/AGENTS.md)
else
    TARGETS=("$@")
fi

PATTERN='status open\|status closed\|status doing\|status pending'

fail=0
for target in "${TARGETS[@]}"; do
    [ -e "$target" ] || continue
    while IFS= read -r match; do
        [ -z "$match" ] && continue
        echo "FAIL [legacy status verb]: $match"
        fail=1
    done < <(grep -rn "$PATTERN" "$target" 2>/dev/null || true)
done

if [ "$fail" -eq 0 ]; then
    echo "OK: no legacy status verbs found"
fi
exit $fail
