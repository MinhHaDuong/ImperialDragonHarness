#!/usr/bin/env bash
# dashboard.sh — raw ticket/PR/branch snapshot of the current repo's origin/main.
# Read-only: fetches, never checks out. One section per block, parseable.
set -euo pipefail

git fetch -q --prune origin

echo "== open tickets (origin/main)"
ids=$(git ls-tree --name-only origin/main tickets/ | grep -oE '/[0-9]{4}-' | tr -d '/-' || true)
echo "count: $(printf '%s\n' "$ids" | grep -c . || true)"
for id in $ids; do
    f=$(git ls-tree --name-only origin/main tickets/ | grep "/$id-")
    body=$(git show "origin/main:$f")
    title=$(printf '%s\n' "$body" | sed -n 's/^Title: *//p' | head -1)
    labels=$(printf '%s\n' "$body" | sed -n 's/^Label: *//p' | paste -sd, -)
    blocked=$(printf '%s\n' "$body" | sed -n 's/^Blocked-by: *//p' | paste -sd, -)
    echo "$id | $title | label=${labels:-} | blocked-by=${blocked:-}"
done

echo "== remote branches"
git branch -r --format='%(refname:short)' | grep -v -e HEAD -e '^origin$' -e '^origin/main$' || true

# ticket 1319: merge requests come from the forge adapter. Exit 3 = no forge, 2 = could not look.
forge_py="$(dirname "$0")/../../scripts/forge.py"
set +e
open=$(python3 "$forge_py" list --state open 2>/dev/null); rc=$?
if [ "$rc" = 0 ]; then
    merged=$(python3 "$forge_py" list --state merged --limit 8 2>/dev/null); rc=$?
fi
set -e
if [ "$rc" = 0 ]; then
    echo "== open merge requests"
    printf '%s' "$open" | python3 -c '
import json, sys
for r in json.load(sys.stdin):
    print(r["number"], r["branch"], "auto=" + str(bool(r["auto"])).lower(), r["title"])'
    echo "== recently merged"
    printf '%s' "$merged" | python3 -c '
import json, sys
for r in json.load(sys.stdin):
    print(r["number"], r["mergedAt"], r["title"])'
elif [ "$rc" = 3 ]; then
    echo "== merge requests: no forge (no origin remote), NOT inspected"
else
    echo "== merge requests: forge CLI unavailable or signed out, NOT inspected"
fi
