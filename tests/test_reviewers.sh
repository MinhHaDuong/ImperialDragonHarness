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
    if printf '%s' "$hay" | grep -qF -- "$needle"; then echo "PASS: $label"; PASS=$((PASS+1))
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

# ── arg validation ───────────────────────────────────────────────────────────
if "$REVIEWERS" request >/dev/null 2>&1; then echo "FAIL: request missing arg should fail"; FAIL=$((FAIL+1)); else echo "PASS: request missing arg fails"; PASS=$((PASS+1)); fi

echo ""; echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
