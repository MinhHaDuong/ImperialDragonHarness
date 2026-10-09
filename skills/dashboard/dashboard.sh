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

if command -v gh >/dev/null; then  # harness-extension-point
    echo "== open merge requests"
    gh pr list --state open --json number,headRefName,title,autoMergeRequest \
        --jq '.[]|"\(.number) \(.headRefName) auto=\(.autoMergeRequest!=null) \(.title)"'  # harness-extension-point
    echo "== recently merged"
    gh pr list --state merged --limit 8 --json number,mergedAt,title \
        --jq '.[]|"\(.number) \(.mergedAt) \(.title)"'  # harness-extension-point
else
    echo "== merge requests: forge CLI unavailable, not inspected"
fi
