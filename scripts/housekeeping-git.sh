#!/usr/bin/env bash
# Run from project root. Handles git sync, beat-skip expiry, and erg DAG check.
set -euo pipefail

git fetch --all --prune --quiet || true
git gc --auto || true

SKIP_FILE=".git/beat-skip.json"
if [[ -f "$SKIP_FILE" ]]; then
    NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    TMP=$(mktemp)
    if jq --arg now "$NOW" '[.[] | select(.until == null or .until > $now)]' "$SKIP_FILE" > "$TMP"; then
        mv "$TMP" "$SKIP_FILE"
    else
        rm -f "$TMP"
    fi
fi

ERG=${ERG:-tickets/erg}
"$ERG" check tickets/ 2>/dev/null || true

exit 0
