#!/usr/bin/env bash
# Standing close-claim grammar regression (ticket 0930).
#
# The fixture table is deliberately data, not a copied parser.  Both real
# consumers run against it through minimal forge stubs: erg-pr-merge proves
# which IDs it would close, while check-close-claims proves which merged PRs it
# examines.  The archived-path row also runs the pre-0929 merge helper extracted
# from git history and must fail there, keeping this a live red regression.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$PWD
FIXTURES="$ROOT/tests/fixtures/close-claim-grammar.tsv"
MERGE="$ROOT/skills/merge/erg-pr-merge"
CHECKER="$ROOT/skills/roar/check-close-claims.sh"
PRE_0929='b2196361^'
fail=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $1"; }
fail_case() { echo "FAIL: $1"; fail=1; }

make_gh_stub() { # <directory>
    mkdir -p "$1/bin"
    cat > "$1/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  'pr view 42 --json number,headRefName,baseRefName,mergeable,statusCheckRollup,body,isDraft,title')
    jq -n --arg body "$STUB_BODY" \
      '{number:42,headRefName:"fixture",baseRefName:"main",mergeable:"MERGEABLE",statusCheckRollup:[],body:$body,isDraft:false,title:"fixture"}' ;;
  'pr view 42 --json state --jq .state') echo MERGED ;;
  'pr merge 42 --merge --auto --delete-branch') exit 0 ;;
  *) echo "stub gh: unexpected invocation: $*" >&2; exit 2 ;;
esac
STUB
    chmod +x "$1/bin/gh"
}

make_erg_stub() { # <directory>
    cat > "$1/bin/erg" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  close) printf '%s\n' "$2" >> "$ERG_CLOSE_LOG" ;;
  archive) : ;;
  *) echo "stub erg: unexpected invocation: $*" >&2; exit 2 ;;
esac
STUB
    chmod +x "$1/bin/erg"
}

seed_merge_repo() { # <directory>
    local repo="$1" id
    git init -q "$repo"
    git -C "$repo" config user.email test@example.com
    git -C "$repo" config user.name test
    git -C "$repo" config commit.gpgsign false
    git -C "$repo" branch -M main
    mkdir -p "$repo/tickets/closed"
    for id in 0001 0003 0004 0005 0006; do
        printf '%%erg 0.1\nTitle: %s\nCreated: 2026-09-16\nAuthor: test\n' "$id" \
            > "$repo/tickets/${id}-fixture.erg"
    done
    printf '%%erg 0.1\nTitle: 0002\nCreated: 2026-09-16\nAuthor: test\nClosed: 2026-09-16 fixture\n' \
        > "$repo/tickets/closed/0002-fixture.erg"
    git -C "$repo" add tickets
    git -C "$repo" commit -q -m fixture
    git init -q --bare "$repo/origin.git"
    git -C "$repo" remote add origin "$repo/origin.git"
    git -C "$repo" push -q -u origin main
    git -C "$repo" switch -q -c fixture
    git -C "$repo" push -q -u origin fixture
}

run_merge() { # <script> <body> <repo> <close-log>
    local script="$1" body="$2" repo="$3" close_log="$4"
    (cd "$repo" && PATH="$TMP/bin:$PATH" ERG="$TMP/bin/erg" ERG_CLOSE_LOG="$close_log" \
        STUB_BODY="$body" ERG_PR_MERGE_SYNC=/bin/true ERG_PR_MERGE_POLL_INTERVAL=0 \
        ERG_PR_MERGE_MERGED_POLL_TRIES=1 bash "$script" 42)
}

make_gh_stub "$TMP"
make_erg_stub "$TMP"

# Each row runs the current merge helper in a real temporary git repository.
# Claims must reach the real helper's close call; the non-claim must stop at its
# explicit no-close-claim guard.  The archived row is already terminal, so the
# helper's observable agreement is its "already closed" path rather than a new
# close mutation.
while IFS='|' read -r label expected escaped_body; do
    [[ -z "$label" || "$label" == \#* ]] && continue
    body=$(printf '%b' "$escaped_body")
    repo="$TMP/merge-$label"
    close_log="$TMP/$label.closes"
    : > "$close_log"
    seed_merge_repo "$repo"
    if out=$(run_merge "$MERGE" "$body" "$repo" "$close_log" 2>&1); then rc=0; else rc=$?; fi

    if [[ "$expected" == '-' ]]; then
        if [[ "$rc" -ne 0 && "$out" == *'no close-claim in PR body'* && ! -s "$close_log" ]]; then
            pass "merge helper leaves $label outside the close grammar"
        else
            fail_case "merge helper misclassified $label (rc $rc): $out"
        fi
        continue
    fi

    if [[ "$rc" -ne 0 ]]; then
        fail_case "merge helper rejected $label (rc $rc): $out"
    elif [[ "$label" == closed-path ]]; then
        [[ "$out" == *'Ticket 0002 is already closed and archived.'* ]] \
            && pass "merge helper accepts $label" \
            || fail_case "merge helper did not recognise $label"
    elif [[ "$(paste -sd, "$close_log")" == "$expected" ]]; then
        pass "merge helper closes $expected for $label"
    else
        fail_case "merge helper extracted '$(paste -sd, "$close_log")' for $label; expected $expected"
    fi
done < "$FIXTURES"

# Historical red proof: before ticket 0929, the archived-path fixture reached
# the no-claim guard instead of the terminal archived-ticket path above.
PRE_MERGE="$TMP/erg-pr-merge-pre-0929"
git show "$PRE_0929:skills/merge/erg-pr-merge" > "$PRE_MERGE"
chmod +x "$PRE_MERGE"
pre_repo="$TMP/pre-0929"
pre_log="$TMP/pre-0929.closes"
: > "$pre_log"
seed_merge_repo "$pre_repo"
closed_body=$(awk -F'|' '$1 == "closed-path" {print $3}' "$FIXTURES")
closed_body=$(printf '%b' "$closed_body")
if pre_out=$(run_merge "$PRE_MERGE" "$closed_body" "$pre_repo" "$pre_log" 2>&1); then pre_rc=0; else pre_rc=$?; fi
if [[ "$pre_rc" -ne 0 && "$pre_out" == *'no close-claim in PR body'* && ! -s "$pre_log" ]]; then
    pass "pre-0929 helper fails the archived-path regression fixture"
else
    fail_case "pre-0929 helper did not expose the archived-path defect (rc $pre_rc): $pre_out"
fi

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
jq "$expr" < "$GH_STUB_PAYLOAD"
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
