#!/usr/bin/env bash
# Standing close-claim grammar regression (ticket 0930).
#
# The fixture table is deliberately data, not a copied parser.  The retained
# reader of the grammar, check-close-claims, runs against it through a minimal
# forge stub and proves which merged PRs' claims it examines.  The merge helper
# that also consumed the table was retired (ticket 1178): the merge recipe
# points to the same grammar (skills/merge/references/claims.md).
set -euo pipefail

# Hermetic children (ticket 0875): the driver and detector are exercised as
# `bash "$script"` / `bash "$CHECKER"`, and such children inherit BASH_ENV —
# re-running the project .env loader inside the very processes under test.
# Nothing here reads project .env values, so clear the loader suite-wide
# (rules/coding-bash.md).
export BASH_ENV=

cd "$(dirname "$0")/.."
ROOT=$PWD
FIXTURES="$ROOT/tests/fixtures/close-claim-grammar.tsv"
CHECKER="$ROOT/skills/roar/check-close-claims.sh"
fail=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $1"; }
fail_case() { echo "FAIL: $1"; fail=1; }

# Feed every row independently to the field detector.  Expected IDs are left
# open, so each extracted ID must produce its own DROPPED finding.  This proves
# identity, not merely an aggregate count that could hide swapped IDs.
make_detector_gh() { # <directory>
    mkdir -p "$1/bin"
    cat > "$1/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
expr=""; previous=""
for arg in "$@"; do
    [[ "$previous" == --jq ]] && expr="$arg"
    previous="$arg"
done
if [[ -n "$expr" ]]; then jq "$expr" < "$GH_STUB_PAYLOAD"; else cat "$GH_STUB_PAYLOAD"; fi
STUB
    chmod +x "$1/bin/gh"
}

recent=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)
n=100
while IFS='|' read -r label expected escaped_body; do
    [[ -z "$label" || "$label" == \#* ]] && continue
    body=$(printf '%b' "$escaped_body")
    detector="$TMP/detector-$label"
    mkdir -p "$detector/tickets"
    # check-close-claims reads merged requests through forge.py, which answers
    # "no forge" (exit 3) without an origin remote: give the fixture one.
    git init -q "$detector" && git -C "$detector" remote add origin https://example.invalid/o/r.git
    make_detector_gh "$detector"
    expected_count=0
    if [[ "$expected" != '-' ]]; then
        IFS=, read -r -a ids <<< "$expected"
        expected_count=${#ids[@]}
        for id in "${ids[@]}"; do
            printf '%%erg 0.1\nTitle: %s\nCreated: 2026-09-16\nAuthor: test\n' "$id" \
                > "$detector/tickets/${id}-fixture.erg"
        done
    fi
    jq -n --argjson number "$n" --arg title "$label" --arg body "$body" --arg merged "$recent" \
        '[{number:$number,title:$title,body:$body,mergedAt:$merged}]' > "$detector/prs.json"
    n=$((n + 1))
    if detector_out=$(cd "$detector" && PATH="$detector/bin:$PATH" GH_STUB_PAYLOAD="$detector/prs.json" bash "$CHECKER" 2>&1); then detector_rc=0; else detector_rc=$?; fi
    if [[ "$expected_count" -eq 0 ]]; then
        expected_rc=0
        expected_summary='0 close claim(s) across 0 PR(s), 0 explicit no-close, 1 unrecognised; 0 finding(s).'
    else
        expected_rc=1
        expected_summary="${expected_count} close claim(s) across 1 PR(s), 0 explicit no-close, 0 unrecognised; ${expected_count} finding(s)."
    fi
    row_ok=1
    [[ "$detector_rc" -eq "$expected_rc" ]] || row_ok=0
    [[ "$detector_out" == *"$expected_summary"* ]] || row_ok=0
    if [[ "$expected" != '-' ]]; then
        for id in "${ids[@]}"; do
            [[ "$detector_out" == *"claims ticket $id"* ]] || row_ok=0
        done
    else
        [[ "$detector_out" != *DROPPED:* ]] || row_ok=0
    fi
    if [[ "$row_ok" -eq 1 ]]; then
        pass "field detector agrees on $label"
    else
        fail_case "field detector drifted on $label (rc $detector_rc): $detector_out"
    fi
done < "$FIXTURES"

exit "$fail"
