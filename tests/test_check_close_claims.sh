#!/usr/bin/env bash
# Tests for skills/roar/check-close-claims.sh (ticket 0903).
#
# The detector's natural output is silence, so silence proves nothing on its
# own: a working detector and one that never looked agree on a clean repo.
# Every fixture here therefore carries a KNOWN-BAD case (a merged PR claiming a
# ticket that has no `Closed:` header) and asserts the detector names it —
# `test 1` is that positive control. `test 5` is its mirror: the same detector
# on a repo where every claim was honoured must go quiet, which is what
# separates "reads the tickets" from "always complains".
#
# `gh` is stubbed, but the stub runs the REAL jq against the canned payload
# using the `--jq` expression the script passes, so the mergedAt window is
# genuinely exercised rather than assumed.
set -euo pipefail

# Hermetic children (ticket 0875): each case runs the detector as
# `bash "$SCRIPT"`, and such a child inherits BASH_ENV — re-running the
# project .env loader inside the very process whose verdicts are under test.
# Nothing here reads project .env values, so clear the loader suite-wide
# (tests/test_bash_tests_are_hermetic.sh) rather than annotate every spawn.
export BASH_ENV=

cd "$(dirname "$0")/.."
SCRIPT="$PWD/skills/roar/check-close-claims.sh"
fail=0

_check_says() { # <label> <output> <substring>
    case "$2" in
        *"$3"*) echo "PASS: $1" ;;
        *) echo "FAIL: $1 — output did not carry '$3'"; fail=1 ;;
    esac
}

_check_lacks() { # <label> <output> <substring>
    case "$2" in
        *"$3"*) echo "FAIL: $1 — output unexpectedly carried '$3'"; fail=1 ;;
        *) echo "PASS: $1" ;;
    esac
}

_check_rc() { # <label> <expected> <actual>
    if [ "$2" = "$3" ]; then
        echo "PASS: $1"
    else
        echo "FAIL: $1 — expected rc $2, got $3"
        fail=1
    fi
}

# --- fixture ---------------------------------------------------------------
# A repo with a ticket store in four states, and a stubbed forge that reports
# five merged PRs against them.
make_repo() { # <dir>
    local d="$1"
    mkdir -p "$d/tickets/closed" "$d/bin"
    # 0001: claimed by a merged PR, never closed — the defect.
    printf '%%erg 0.1\nTitle: dropped\nCreated: 2026-09-01\nAuthor: t\n' > "$d/tickets/0001-dropped.erg"
    # 0002: claimed and closed in place (closed but not yet archived).
    printf '%%erg 0.1\nTitle: honoured\nCreated: 2026-09-01\nAuthor: t\nClosed: 2026-09-09 PR #102\n' > "$d/tickets/0002-honoured.erg"
    # 0003: claimed, closed and archived — the normal end state.
    printf '%%erg 0.1\nTitle: archived\nCreated: 2026-09-01\nAuthor: t\nClosed: 2026-09-09 PR #103\n' > "$d/tickets/closed/0003-archived.erg"
}

make_gh_stub() { # <dir> <payload-file>
    cat > "$1/bin/gh" <<'STUB'
#!/usr/bin/env bash
# Minimal gh stand-in: serves the canned payload, applying the caller's --jq
# expression with the real jq so the mergedAt filter is actually tested.
expr=""
prev=""
for a in "$@"; do
    [ "$prev" = "--jq" ] && expr="$a"
    prev="$a"
done
if [ -n "$expr" ]; then
    jq "$expr" < "$GH_STUB_PAYLOAD"
else
    cat "$GH_STUB_PAYLOAD"
fi
STUB
    chmod +x "$1/bin/gh"
}

RECENT=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)
OLD=$(date -u -d '90 days ago' +%Y-%m-%dT%H:%M:%SZ)

# --- 1. The positive control: a dropped close claim must be named -----------
repo=$(mktemp -d)
make_repo "$repo"
make_gh_stub "$repo" ""
cat > "$repo/prs.json" <<EOF
[
  {"number":101,"title":"fix the thing","mergedAt":"$RECENT",
   "body":"Some text\n\n**Ticket:** tickets/0001-dropped.erg\n"},
  {"number":102,"title":"closed in place","mergedAt":"$RECENT",
   "body":"**Ticket:** tickets/0002-honoured.erg\n"},
  {"number":103,"title":"archived normally","mergedAt":"$RECENT",
   "body":"**Ticket:** tickets/0003-archived.erg\n"},
  {"number":104,"title":"no ticket","mergedAt":"$RECENT",
   "body":"Ticket: none\n"},
  {"number":105,"title":"references without closing","mergedAt":"$RECENT",
   "body":"Ticket-ref: tickets/0001-dropped.erg\n"}
]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?

_check_rc "a dropped close claim makes the detector exit 1" 1 "$rc"
_check_says "…and it names the PR" "$out" "PR #101"
_check_says "…and the ticket" "$out" "ticket 0001"
_check_lacks "a ticket closed in place is not reported" "$out" "PR #102"
_check_lacks "an archived ticket is not reported" "$out" "PR #103"
_check_lacks "'Ticket: none' is not reported" "$out" "PR #104"
# The regex guard: `Ticket-ref:` references without closing, so PR #105 must not
# be read as a claim even though its line contains the word Ticket and a path.
_check_lacks "'Ticket-ref:' is not read as a close claim" "$out" "PR #105"
_check_says "the run reports what it examined" "$out" "examined 5 PRs"
# The buckets must partition the examined set: 3 claims + 2 no-close + 0
# unrecognised = 5. A gap here would mean the script silently checks less than
# it reports, which is the failure shape the whole ticket is about.
_check_says "…and the buckets account for every PR" "$out" \
    "3 close claim(s) across 3 PR(s), 2 explicit no-close, 0 unrecognised"

# One PR may claim several tickets. Count claims, not just PRs carrying claims.
cat > "$repo/prs.json" <<EOF
[{"number":106,"title":"two tickets","mergedAt":"$RECENT",
  "body":"**Ticket:** tickets/0002-honoured.erg\n**Ticket:** tickets/0003-archived.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "two honoured claims exit cleanly" 0 "$rc"
_check_says "the sweep counts both claims on one PR" "$out" "2 close claim(s)"

# An archived path alone is insufficient: a botched rename can move the
# pre-close blob, leaving the ticket in closed/ without its Closed: header.
printf '%%erg 0.1\nTitle: moved without close\nCreated: 2026-09-01\nAuthor: t\n' \
    > "$repo/tickets/closed/0004-missing-header.erg"
cat > "$repo/prs.json" <<EOF
[{"number":107,"title":"bad archive","mergedAt":"$RECENT",
  "body":"**Ticket:** tickets/0004-missing-header.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "archived ticket without Closed header exits 1" 1 "$rc"
_check_says "the bad archive is named as dropped" "$out" "DROPPED: PR #107 claims ticket 0004"

# --- 2. A claim on a ticket that is not in the tree at all -----------------
cat > "$repo/prs.json" <<EOF
[{"number":110,"title":"claims a ghost","mergedAt":"$RECENT",
  "body":"**Ticket:** tickets/0099-ghost.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a claim on an absent ticket exits 1" 1 "$rc"
_check_says "…reported as UNRESOLVED, not DROPPED" "$out" "UNRESOLVED: PR #110"

# Ticket 0929: the closed/ spelling must still identify a dropped claim.
cat > "$repo/prs.json" <<EOF
[{"number":111,"title":"closed path dropped","mergedAt":"$RECENT",
  "body":"**Ticket:** tickets/closed/0001-dropped.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "closed-path dropped claim exits 1" 1 "$rc"
_check_says "closed-path claim identifies the open ticket" "$out" "DROPPED: PR #111 claims ticket 0001"

# Mis-cased paths are accepted consistently by both parser stages.
cat > "$repo/prs.json" <<EOF
[{"number":112,"title":"mixed case claim","mergedAt":"$RECENT",
  "body":"Ticket: TICKETS/Closed/0001-dropped.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "mixed-case dropped claim exits 1" 1 "$rc"
_check_says "mixed-case path retains its ID" "$out" "DROPPED: PR #112 claims ticket 0001"

# An unknown Ticket path is a finding, even beside an explicit no-close line.
cat > "$repo/prs.json" <<EOF
[{"number":113,"title":"bad claim path","mergedAt":"$RECENT",
  "body":"Ticket: tickets/archive/0001-dropped.erg\nTicket: none\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "unparseable claim exits 1" 1 "$rc"
_check_says "unparseable claim is named" "$out" "UNPARSEABLE: PR #113"
_check_says "unparseable claim is not no-close" "$out" "0 explicit no-close, 1 unrecognised"

jq -n --arg merged "$RECENT" --arg body $'Example:\n```markdown\n**Ticket:** tickets/0001-dropped.erg\n```\nTicket: none\n' \
    '[{number:114,title:"fenced example",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "fenced claim example is ignored" 0 "$rc"
_check_says "fenced example is counted as no-close" "$out" "0 close claim(s) across 0 PR(s), 1 explicit no-close"

# Ticket 1152: the sweep shares erg-pr-merge's fence tracker. A `~~~` line
# inside a backtick fence does not close it, so the fenced claim stays inert.
jq -n --arg merged "$RECENT" --arg body $'Example:\n```markdown\n~~~\n**Ticket:** tickets/0001-dropped.erg\n~~~\n```\nTicket: none\n' \
    '[{number:115,title:"tilde in backtick",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a ~~~ line inside a backtick fence keeps its claim inert" 0 "$rc"
_check_lacks "…and nothing is reported dropped" "$out" "DROPPED"

# An unclosed fence must not hide a claim from the audit: erg-pr-merge refuses
# such a body, so a merged one came by another route and is exactly the case
# this sweep exists to name.
jq -n --arg merged "$RECENT" --arg body $'Summary.\n\n```attribution\nkind: review-attribution\n\n**Ticket:** tickets/0001-dropped.erg\n' \
    '[{number:116,title:"unclosed fence",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a claim after an unclosed fence is audited" 1 "$rc"
_check_says "…and named as dropped" "$out" "DROPPED: PR #116 claims ticket 0001"

# Closer indentation is an absolute 3-column limit (opener at 2, closer-like
# line at 5; opener at 3, closer-like line at 4): the claim stays fenced.
# Removing the indent rule must turn this red.
jq -n --arg merged "$RECENT" --arg body $'  ```\n     ```\n**Ticket:** tickets/0001-dropped.erg\n  ```\nTicket: none\n' \
    '[{number:117,title:"deep closer",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a 5-column fence-like line does not close a 2-column fence" 0 "$rc"
jq -n --arg merged "$RECENT" --arg body $'   ```\n    ```\nTicket: tickets/0001-dropped.erg\n   ```\nTicket: none\n' \
    '[{number:118,title:"deep closer 3",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a 4-space fence-like line does not close a 3-column fence" 0 "$rc"

# Tabs advance to the next multiple of 4: space+tab closer is 7 columns and
# validly closes a list-nested fence, so the claim after it is live.
jq -n --arg merged "$RECENT" --arg body $'1.  item\n\n    ```\n \t   ```\n\nTicket: tickets/0001-dropped.erg\n' \
    '[{number:119,title:"mixed tab",mergedAt:$merged,body:$body}]' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a space+tab closer closes a list-nested fence" 1 "$rc"
_check_says "…and the live claim is audited" "$out" "DROPPED: PR #119 claims ticket 0001"

# The tracker is copied, not sourced (each skill script stays standalone), so
# the two copies must stay byte-identical.
_fence_map_body() { sed -n '/^fence_map() {$/,/^}$/p' "$1"; }
merge_fm=$(_fence_map_body skills/merge/erg-pr-merge)
roar_fm=$(_fence_map_body "$SCRIPT")
if [ -n "$merge_fm" ] && [ "$merge_fm" = "$roar_fm" ]; then
    echo "PASS: fence_map is identical in erg-pr-merge and check-close-claims.sh"
else
    echo "FAIL: fence_map copies differ or are missing"; fail=1
fi

# --- 3. The mergedAt window is real, not assumed --------------------------
cat > "$repo/prs.json" <<EOF
[{"number":120,"title":"merged long ago","mergedAt":"$OLD",
  "body":"**Ticket:** tickets/0001-dropped.erg\n"}]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a PR outside the window is not examined" 0 "$rc"
_check_says "…and the zero-examined case says so out loud" "$out" "zero PRs examined"

# --- 4. 'Could not look' must not read as 'all clear' ---------------------
# An empty forge response exits 2, never 0: the whole point of this script is
# that a dropped close and a clean merge leave identical evidence, so a blind
# run must not add a third indistinguishable case.
printf '' > "$repo/prs.json"
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "an empty forge response exits 2, not 0" 2 "$rc"
_check_says "…and says it is not an all-clear" "$out" "NOT an all-clear"

# A repo with no ticket store is simply not this script's business.
bare=$(mktemp -d)
mkdir -p "$bare/bin"
make_gh_stub "$bare" ""
printf '[]' > "$bare/prs.json"
out=$( cd "$bare" && PATH="$bare/bin:$PATH" GH_STUB_PAYLOAD="$bare/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "a repo with no tickets/ exits 0 quietly" 0 "$rc"
rm -rf "$bare"

# --- 5. The mirror of test 1: every claim honoured → silence ---------------
# Without this, a detector hard-wired to complain would pass test 1.
cat > "$repo/prs.json" <<EOF
[
  {"number":130,"title":"closed in place","mergedAt":"$RECENT",
   "body":"**Ticket:** tickets/0002-honoured.erg\n"},
  {"number":131,"title":"archived","mergedAt":"$RECENT",
   "body":"**Ticket:** tickets/0003-archived.erg\n"}
]
EOF
out=$( cd "$repo" && PATH="$repo/bin:$PATH" GH_STUB_PAYLOAD="$repo/prs.json" bash "$SCRIPT" 2>&1 ) && rc=0 || rc=$?
_check_rc "all claims honoured exits 0" 0 "$rc"
_check_lacks "…with no DROPPED line" "$out" "DROPPED"
_check_says "…and still reports the count it examined" "$out" "2 close claim(s)"

rm -rf "$repo"
exit $fail
