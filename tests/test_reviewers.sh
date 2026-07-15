#!/usr/bin/env bash
# Tests for the /reviewers skill dispatcher (review-is-CI wiring).
# Covers: empty-roster no-op; a configured seat firing the (stubbed)
# 0217 seat-runner; per-seat fail-open; harvest normalization to the 0205
# contract shape with a WARN on unparseable input; scorecard appending a
# valid erg log line.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REVIEWERS="${REPO_ROOT}/skills/reviewers/reviewers.sh"
PASS=0; FAIL=0
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then echo "PASS: $label"; PASS=$((PASS+1))
    else echo "FAIL: $label"; echo "  expected: $(printf '%q' "$expected")"; echo "  actual:   $(printf '%q' "$actual")"; FAIL=$((FAIL+1)); fi
}
assert_contains() {
    local label="$1" needle="$2" hay="$3"
    # Pure-bash substring match, no subprocess: the quoted needle is a literal
    # (glob-free) comparison, identical to `grep -F`. Supersedes the here-string
    # `grep -qF <<<` form — a per-call grep subprocess reading a here-string
    # tmpfile intermittently returned no-match under parallel load (ticket 0329);
    # the bash builtin has neither pipe nor tmpfile.
    if [[ "$hay" == *"$needle"* ]]; then echo "PASS: $label"; PASS=$((PASS+1))
    else echo "FAIL: $label (missing: $needle)"; echo "  in: $hay"; FAIL=$((FAIL+1)); fi
}
assert_exit_0() { local label="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS: $label"; PASS=$((PASS+1)); else echo "FAIL: $label (exit $?)"; FAIL=$((FAIL+1)); fi; }

# ── empty-roster roster (default behaviour) ──────────────────────────────────
EMPTY="$WORK/empty.yml"; printf 'reviewers: []\n' > "$EMPTY"

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" list)
assert_eq "list: empty roster" "no reviewers configured" "$out"

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" request 42)
assert_eq "request: empty roster" "no reviewers configured" "$out"
assert_exit_0 "request: empty roster exits 0" env REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" request 42

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" harvest 42)
assert_eq "harvest: empty roster, empty output" "" "$out"

# ── configured roster + stub seat-runner ─────────────────────────────────────
ROSTER="$WORK/panel.yml"
cat > "$ROSTER" <<'YAML'
reviewers:
  - name: stub-good
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
  - name: stub-bad
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML

# Stub seat-runner: 'stub-bad' (by --out basename) exits non-zero to exercise
# fail-open; everyone else emits one contract-shaped FINDING + a SUMMARY.
STUB="$WORK/seat-runner-stub.sh"
cat > "$STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""; while [ $# -gt 0 ]; do [ "$1" = "--out" ] && { out="$2"; shift 2; continue; }; shift; done
name="$(basename "$out" .findings)"
if [ "$name" = "stub-bad" ]; then echo "stub: boom" >&2; exit 1; fi
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one"; echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$STUB"

list_out=$(REVIEWERS_PANEL="$ROSTER" "$REVIEWERS" list)
assert_contains "list: shows configured seat" "stub-good" "$list_out"

FDIR="$WORK/findings"
req_err=$(REVIEWERS_PANEL="$ROSTER" SEAT_RUNNER="$STUB" REVIEWERS_FINDINGS_DIR="$FDIR" \
          REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: good seat ran" "seat 'stub-good' ok" "$req_err"
assert_contains "request: bad seat fail-open WARN" "WARN seat 'stub-bad' failed" "$req_err"
assert_eq "request: good seat wrote findings" "yes" "$([ -s "$FDIR/42/stub-good.findings" ] && echo yes || echo no)"

harv_out=$(REVIEWERS_PANEL="$ROSTER" REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 42 2>/dev/null)
assert_contains "harvest: normalized to contract shape" "verifiable: foo.sh:10 — off-by-one" "$harv_out"
assert_contains "harvest: tags the seat" "[stub-good]" "$harv_out"

# Unparseable input → WARN, not silently dropped.
mkdir -p "$FDIR/99"; printf 'garbage line not a finding\n' > "$FDIR/99/x.findings"
harv_warn=$(REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 99 2>&1 >/dev/null)
assert_contains "harvest: WARN on non-contract line" "WARN non-contract line" "$harv_warn"

# ── template-echo detection ─────────────────────────────────────────────────
mkdir -p "$FDIR/200"
cat > "$FDIR/200/noisy-seat.findings" <<'NOISY'
FINDING|severity=verifiable-or-consider|file=PATH:LINE|rationale=ONE SENTENCE
FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one
FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one
FINDING|severity=consider|file=bar.py:5|rationale=unused import
SUMMARY|findings=1|verdict=approve-or-revise
NOISY
harv_out=$(REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 200 2>/dev/null)
harv_err=$(REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 200 2>&1 >/dev/null)
# Template-echo line must be dropped, not emitted as a finding.
if [[ "$harv_out" == *'verifiable-or-consider'* ]]; then
    echo "FAIL: harvest: template-echo leaked through"; FAIL=$((FAIL+1))
else
    echo "PASS: harvest: template-echo dropped"; PASS=$((PASS+1))
fi
assert_contains "harvest: template-echo logged as DROP" "DROP template-echo" "$harv_err"
# Duplicate collapsed: only one copy of off-by-one.
count=$(printf '%s\n' "$harv_out" | grep -c 'off-by-one' || true)
assert_eq "harvest: duplicate collapsed to one" "1" "$count"
assert_contains "harvest: duplicate logged as DROP" "DROP duplicate" "$harv_err"
# Both real unique findings survive.
assert_contains "harvest: real finding 1 survives" "verifiable: foo.sh:10 — off-by-one" "$harv_out"
assert_contains "harvest: real finding 2 survives" "consider: bar.py:5 — unused import" "$harv_out"

# ── scorecard appends a valid erg log line ───────────────────────────────────
# Build a throwaway erg ticket store so the real erg accepts the note.
ERG_BIN="${REPO_ROOT}/tickets/erg"
if [ -x "$ERG_BIN" ]; then
    TSTORE="$WORK/tickets"; mkdir -p "$TSTORE"; cp "$ERG_BIN" "$TSTORE/erg"
    cat > "$TSTORE/0207-agnostic-cli-reviewer-seat-one-config-op.erg" <<'ERG'
%erg 0.1
Title: Fixture
Created: 2026-06-05
Author: test

--- log ---
2026-06-05T00:00Z test created

--- body ---
## Context
Fixture.
ERG
    SCROSTER="$WORK/sc.yml"
    cat > "$SCROSTER" <<YAML
reviewers:
  - name: stub-good
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML
    ( cd "$WORK" && REVIEWERS_PANEL="$SCROSTER" ERG="$TSTORE/erg" \
        "$REVIEWERS" scorecard 42 stub-good "PASS — 0 verifiable, 2 consider" ) >/dev/null 2>&1
    if "$TSTORE/erg" validate "$TSTORE/0207-agnostic-cli-reviewer-seat-one-config-op.erg" >/dev/null 2>&1 \
       && grep -q 'MR #42 seat=stub-good' "$TSTORE/0207-agnostic-cli-reviewer-seat-one-config-op.erg"; then
        echo "PASS: scorecard appends a valid erg log line"; PASS=$((PASS+1))
    else
        echo "FAIL: scorecard did not append a valid erg log line"; FAIL=$((FAIL+1))
    fi
else
    echo "SKIP: erg binary absent — scorecard erg-integration test"
fi

# ── credential-env threads from roster to seat-runner (0207) ─────────────────
# A seat carrying `credential-env: NAME` must pass `--credential-env NAME` to
# the seat-runner; a seat without it must NOT pass the flag. The stub captures
# each seat's full argv so both cases are checked against real invocations.
CE_STUB="$WORK/seat-runner-ce-stub.sh"
cat > "$CE_STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
argv="$*"; out=""
while [ $# -gt 0 ]; do [ "$1" = "--out" ] && { out="$2"; shift 2; continue; }; shift; done
name="$(basename "$out" .findings)"
printf '%s\n' "$argv" > "${out%.findings}.argv"
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=x"; echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$CE_STUB"

CEROSTER="$WORK/ce.yml"
cat > "$CEROSTER" <<'YAML'
reviewers:
  - name: seat-with-cred
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: https://openrouter.ai/api/v1
    model: openai/stub
    credential-env: MY_ROSTER_KEY
  - name: seat-no-cred
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML

CEDIR="$WORK/ce-findings"
REVIEWERS_PANEL="$CEROSTER" SEAT_RUNNER="$CE_STUB" REVIEWERS_FINDINGS_DIR="$CEDIR" \
    REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 77 >/dev/null 2>&1
assert_contains "request: credential-env seat passes the flag through" \
    "--credential-env MY_ROSTER_KEY" "$(cat "$CEDIR/77/seat-with-cred.argv" 2>/dev/null || true)"
if grep -qF -- '--credential-env' "$CEDIR/77/seat-no-cred.argv" 2>/dev/null; then
    echo "FAIL: request: no-cred seat must not pass --credential-env"; FAIL=$((FAIL+1))
else
    echo "PASS: request: no-cred seat omits --credential-env"; PASS=$((PASS+1))
fi

# ── forge-bot seat: on-demand request via the forge review API (0206) ────────
# A forge-bot seat has no seat-runner; `request` asks the forge to run its
# server-side reviewer on the PR. Stub `gh` to capture the call.
GHBOT="$WORK/ghbin"; mkdir -p "$GHBOT"
cat > "$GHBOT/gh" <<'GHSTUB'
#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "$GH_CALL_LOG"
[ -n "${GH_FAIL:-}" ] && exit 1
exit 0
GHSTUB
chmod +x "$GHBOT/gh"

BOTROSTER="$WORK/bot.yml"
cat > "$BOTROSTER" <<'YAML'
reviewers:
  - name: copilot
    kind: forge-bot
    status: advisory
    login: copilot-pull-request-reviewer[bot]
    trial-ticket: tickets/0206-copilot-review-in-the-verify-panel-on-demand.erg
YAML

GHLOG="$WORK/gh-calls.log"; : > "$GHLOG"
bot_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" \
          REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" \
          "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot seat requested" "forge-bot seat 'copilot' requested" "$bot_err"
assert_contains "request: forge API call carries the login" "copilot-pull-request-reviewer[bot]" "$(cat "$GHLOG")"
assert_contains "request: forge API call targets the PR" "pulls/42/requested_reviewers" "$(cat "$GHLOG")"

# Forge API failure → WARN, fail-open (exit 0).
bot_fail_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" GH_FAIL=1 \
               REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" \
               "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot failure fail-open WARN" "WARN forge-bot seat 'copilot'" "$bot_fail_err"
assert_exit_0 "request: forge-bot failure exits 0" env PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" GH_FAIL=1 \
    REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 42

# A forge-bot seat with no login → WARN, skipped, others unaffected.
NOLOGIN="$WORK/nologin.yml"
cat > "$NOLOGIN" <<'YAML'
reviewers:
  - name: mystery-bot
    kind: forge-bot
    status: advisory
    trial-ticket: tickets/0206-copilot-review-in-the-verify-panel-on-demand.erg
YAML
nologin_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" \
              REVIEWERS_PANEL="$NOLOGIN" REVIEWERS_PR_BRANCH="some-branch" \
              "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot without login WARNs" "WARN forge-bot seat 'mystery-bot' has no login" "$nologin_err"

# ── scores: read-back of trial scorecards + audition blocks (0348) ───────────
# scores greps the fixed-schema trial lines out of the ticket store — corpus
# wide, including tickets/closed/ — and prints one sortable table. Read-only:
# it never edits a roster or writes an erg-log line. Prove the closed/ search
# by putting the scorecard lines only in a closed ticket.
STICK="$WORK/score-tickets"; mkdir -p "$STICK/closed"
cat > "$STICK/0207-trial.erg" <<'ERG'
%erg 0.1
Title: Trial fixture
Created: 2026-07-14
Author: test

--- log ---
2026-07-14T20:15Z claude note audition candidate=hy3-free model=openai/tencent/hy3:free board=10MR findings=59 duplicate=23 unique-verified=0 unique-hallucinated=36 overlap=38% latency=3419.1s cost=n/a
2026-07-14T20:16Z claude note audition candidate=broken model=x board=1MR

--- body ---
## Context
Fixture.
ERG
cat > "$STICK/closed/0206-copilot.erg" <<'ERG'
%erg 0.1
Title: Copilot trial fixture
Created: 2026-07-13
Author: test
Closed: 2026-07-13

--- log ---
2026-07-13T19:43Z claude note MR ImperialDragonHarness#537 seat=copilot verdict: PASS — 0 verifiable, 1 consider (memory consolidation)
2026-07-13T19:43Z claude note MR ImperialDragonHarness#559 seat=copilot verdict: PASS — 0 verifiable, 0 consider (accurate summary)
2026-07-13T19:44Z claude note MR ImperialDragonHarness#560 seat=copilot verdict: PASS — 1 verifiable, 2 consider (rejected 9 verifiable-looking; noted 7 consider-style nits in prose)
2026-07-13T19:45Z claude note MR ImperialDragonHarness#561 seat=copilot verdict: rejected 8 verifiable, all bogus — true 4 verifiable, 6 consider (final)

--- body ---
## Context
A ticket body may quote the card schema as documentation, e.g.
audition candidate=doc-example model=x board=99MR findings=1 duplicate=1 unique-verified=1 unique-hallucinated=1 overlap=100% latency=1.0s cost=n/a
and MR #0 seat=doc-example verdict: PASS — 5 verifiable, 5 consider (illustration).
These body lines MUST NOT appear in the table (ticket 0348: scan log only).

## Format example
A trial ticket's log section is delimited like this:
--- log ---
2026-01-01T00:00Z claude note MR phantom#1 seat=ghost verdict: PASS — 9 verifiable, 9 consider (body re-entry decoy — must be ignored)
ERG

scores_out=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores 2>/dev/null)
assert_contains "scores: header names OVERLAP column" "OVERLAP" "$scores_out"
assert_contains "scores: lists audition candidate" "hy3-free" "$scores_out"
assert_contains "scores: audition row carries findings count" "59" "$scores_out"
assert_contains "scores: finds scorecard seat in closed/ ticket" "copilot" "$scores_out"
assert_contains "scores: scorecard row carries the MR ident" "ImperialDragonHarness#537" "$scores_out"

# Greedy-regex poison guard: a verdict whose freeform prose contains later
# "<digit> verifiable/consider" phrases must still report the TRUE counts (1/2),
# taken from the first occurrence — not 9/7 from the parenthetical (0348 review).
poison_row=$(printf '%s\n' "$scores_out" | grep 'ImperialDragonHarness#560')
assert_contains "scores: count taken from first occurrence, not poisoned by prose" \
    " 1     2 " "$poison_row"
if [[ "$poison_row" == *" 9 "* || "$poison_row" == *" 7 "* ]]; then
    echo "FAIL: scores: freeform verdict prose poisoned the VERIF/CONS count"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: freeform verdict prose did not poison the count"; PASS=$((PASS+1))
fi

# Poison-BEFORE guard: freeform prose carrying "<digit> verifiable" BEFORE the
# real tally must not poison the count either — the counts come from the anchored
# "N verifiable, M consider" unit (0348 review round 2). True tally is 4/6.
poison2_row=$(printf '%s\n' "$scores_out" | grep 'ImperialDragonHarness#561')
assert_contains "scores: count anchored to the real tally, not leading prose" \
    " 4     6 " "$poison2_row"
if [[ "$poison2_row" == *" 8 "* ]]; then
    echo "FAIL: scores: leading verdict prose poisoned the count"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: leading verdict prose did not poison the count"; PASS=$((PASS+1))
fi

# Log-section-only guard: cards quoted in a ticket BODY are documentation, not
# real trial results — they must never surface as table rows (0348 review).
if [[ "$scores_out" == *"doc-example"* ]]; then
    echo "FAIL: scores: a body-quoted card leaked into the table"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: body-quoted cards excluded (log section only)"; PASS=$((PASS+1))
fi

# Body re-entry guard: a body line quoting "--- log ---" must NOT re-open the
# scan — the phantom#1/ghost card sits after the real body boundary (0348 r2).
if [[ "$scores_out" == *"ghost"* || "$scores_out" == *"phantom"* ]]; then
    echo "FAIL: scores: body-quoted '--- log ---' re-opened the scan (phantom row)"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: body-quoted '--- log ---' did not re-open the scan"; PASS=$((PASS+1))
fi

# Filter to one name → only that seat/candidate; the other kind is excluded.
scores_filt=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores copilot 2>/dev/null)
assert_contains "scores: filter shows the requested seat" "copilot" "$scores_filt"
if [[ "$scores_filt" == *"hy3-free"* ]]; then
    echo "FAIL: scores: filter leaked a non-matching candidate"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: filter excludes non-matching rows"; PASS=$((PASS+1))
fi

# A malformed trial line WARNs on stderr, never silently dropped.
scores_warn=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores 2>&1 >/dev/null)
assert_contains "scores: WARN on malformed line" "WARN" "$scores_warn"

# scores is read-only: it must not mutate the ticket store.
before=$(cat "$STICK/0207-trial.erg" "$STICK/closed/0206-copilot.erg")
REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores >/dev/null 2>&1
after=$(cat "$STICK/0207-trial.erg" "$STICK/closed/0206-copilot.erg")
assert_eq "scores: leaves the ticket store unchanged" "$before" "$after"

# ── help: explicit verb, exit 0, names every subcommand (0348) ───────────────
assert_exit_0 "help: exits 0" "$REVIEWERS" help
help_out=$("$REVIEWERS" help 2>/dev/null)
for verb in list request harvest scorecard audition scores help; do
    assert_contains "help: names '$verb'" "$verb" "$help_out"
done
# No-arg still exits 1 (the unknown/no-verb fallback is unchanged).
if "$REVIEWERS" >/dev/null 2>&1; then echo "FAIL: no-arg should still exit 1"; FAIL=$((FAIL+1)); else echo "PASS: no-arg still exits 1"; PASS=$((PASS+1)); fi

# ── arg validation ───────────────────────────────────────────────────────────
if "$REVIEWERS" request >/dev/null 2>&1; then echo "FAIL: request missing arg should fail"; FAIL=$((FAIL+1)); else echo "PASS: request missing arg fails"; PASS=$((PASS+1)); fi

echo ""; echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
