#!/bin/bash
set -euo pipefail
# Warn if any rule file hasn't been reviewed in 30+ days.
# Covers rules/*.md and one level of subdirectory (prose/, doctype/, lang/, typo/):
# a narrow rules/*.md glob left seven subdirectory rules unmonitored.
# Advisory only — always exits 0.

STALE_DAYS=30
now=$(date +%s)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

for f in "$PLUGIN_ROOT"/rules/*.md "$PLUGIN_ROOT"/rules/*/*.md; do
    [ -e "$f" ] || continue          # unmatched glob expands to itself
    date_str=$(grep -oP 'last-reviewed:\s*\K\d{4}-\d{2}-\d{2}' "$f" 2>/dev/null || true)
    [ -z "$date_str" ] && continue
    reviewed=$(date -d "$date_str" +%s 2>/dev/null) || continue
    age_days=$(( (now - reviewed) / 86400 ))
    if [ "$age_days" -ge "$STALE_DAYS" ]; then
        # path relative to rules/, so doctype/book.md and lang/en.md stay distinct
        echo "STALE RULE: ${f#"$PLUGIN_ROOT"/rules/} last reviewed $date_str ($age_days days ago)"
    fi
done

exit 0
