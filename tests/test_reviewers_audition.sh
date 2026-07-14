#!/usr/bin/env bash
# Tests for `/reviewers audition` (ticket 0346) — the retrospective benchmark
# board that replays a candidate model over already-merged PRs and classifies
# each finding against ground truth.
#
# Covers, over a 2-PR TOY board with KNOWN ground truth and a stubbed
# OpenAI-compatible seat (the 0217 seat-runner is replaced via SEAT_RUNNER):
#   - three-way classification: duplicate / unique-verified / unique-hallucinated
#   - wildcard (`file:*`) panel anchor matches any line in the file
#   - scorecard block shape (findings / overlap% / latency / $ per review)
#   - the scorecard is logged to the trial ticket via `erg log note`
#   - fail-loud: a seat-runner that cannot reach its endpoint exits non-zero
#   - the roster is never touched (panel.yml byte-identical after two runs)
#
# SKIP convention mirrors tests/test_reviewers.sh: echo "SKIP: reason" and keep
# going; a genuine defect FAILs.
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
    # Pure-bash substring match, no subprocess (mirrors test_reviewers.sh).
    if [[ "$hay" == *"$needle"* ]]; then echo "PASS: $label"; PASS=$((PASS+1))
    else echo "FAIL: $label (missing: $needle)"; echo "  in: $hay"; FAIL=$((FAIL+1)); fi
}

# ── toy board: 2 PRs with known ground truth ─────────────────────────────────
# Anchors are basename[:line|:*] (the board is stored basename-normalized so it
# stays forge/stack-agnostic; the classifier matches candidate findings by
# basename + line). PR1 exercises a line-precise panel anchor, a `:*` wildcard
# panel anchor, and a defect (panel-missed) anchor; PR2 has an empty defect set.
# PR1's title carries a literal `|`: the parser must not let it shift the
# pipe-delimited record and corrupt the panel field (regression guard).
BOARD="$WORK/board.yml"
cat > "$BOARD" <<'YAML'
# Toy benchmark board.
board:
  - pr: 1
    title: "toy | one with a pipe"
    base: deadbeef1
    head: cafebabe1
    panel: alpha.sh:10 beta.sh:*
    defects: gamma.sh:20
  - pr: 2
    title: "toy two"
    base: deadbeef2
    head: cafebabe2
    panel: delta.py:5
    defects:
YAML

# ── stub seat-runner: canned findings per board PR (keyed on --out basename) ──
# PR1 emits: alpha.sh:10 (dup, line-precise), beta.sh:77 (dup, wildcard match),
#            gamma.sh:20 (unique-verified, matches the defect anchor),
#            zeta.sh:99 (unique-hallucinated, matches nothing).
# PR2 emits: delta.py:5 (dup), epsilon.py:1 (unique-hallucinated).
# Both emit a SUMMARY line carrying token counts so the cost field is exercised.
STUB="$WORK/seat-stub.sh"
cat > "$STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""
while [ $# -gt 0 ]; do case "$1" in --out) out="$2"; shift 2 ;; *) shift ;; esac; done
pr="$(basename "$out" .findings)"
case "$pr" in
  1) { echo "FINDING|severity=verifiable|file=src/alpha.sh:10|rationale=dup-line"
       echo "FINDING|severity=verifiable|file=src/beta.sh:77|rationale=dup-wildcard"
       echo "FINDING|severity=verifiable|file=src/gamma.sh:20|rationale=panel-missed-real"
       echo "FINDING|severity=consider|file=src/zeta.sh:99|rationale=hallucinated"
       echo "SUMMARY|findings=4|verdict=revise|prompt_tokens=1000|completion_tokens=200"
     } > "$out" ;;
  2) { echo "FINDING|severity=verifiable|file=lib/delta.py:5|rationale=dup-line"
       echo "FINDING|severity=consider|file=lib/epsilon.py:1|rationale=hallucinated"
       echo "SUMMARY|findings=2|verdict=approve|prompt_tokens=500|completion_tokens=100"
     } > "$out" ;;
esac
STUBEOF
chmod +x "$STUB"

# ── fixture ticket store so the real erg accepts the scorecard note ──────────
# erg resolves its ticket store from the erg binary's own location, so the
# fixture erg MUST live in the throwaway store (mirrors test_reviewers.sh's
# scorecard test) — otherwise the note lands in the repo's real tickets/.
ERG_BIN="${REPO_ROOT}/tickets/erg"
TDIR="$WORK/run"; mkdir -p "$TDIR/tickets"
[ -x "$ERG_BIN" ] && cp "$ERG_BIN" "$TDIR/tickets/erg"
ERG_FIXTURE="$TDIR/tickets/erg"
TRIAL="tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg"
cat > "$TDIR/tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg" <<'ERG'
%erg 0.1
Title: Fixture trial ticket
Created: 2026-06-05
Author: test

--- log ---
2026-06-05T00:00Z test created

--- body ---
## Context
Fixture.
ERG

# A sentinel roster so we can prove audition never mutates it.
SENTINEL="$TDIR/skills/reviewers/panel.yml"; mkdir -p "$(dirname "$SENTINEL")"
printf 'reviewers: []\n' > "$SENTINEL"
sentinel_before="$(cat "$SENTINEL")"

# ── run audition over the toy board ──────────────────────────────────────────
FDIR="$WORK/findings"
if [ -x "$ERG_BIN" ]; then
    card="$( cd "$TDIR" && \
        REVIEWERS_FINDINGS_DIR="$FDIR" SEAT_RUNNER="$STUB" ERG="$ERG_FIXTURE" \
        REVIEWERS_PRICE_IN_PER_M=1 REVIEWERS_PRICE_OUT_PER_M=2 \
        "$REVIEWERS" audition openai/toy-candidate \
            --board "$BOARD" --endpoint http://127.0.0.1:9/v1 \
            --trial-ticket "$TRIAL" --name toy-cand 2>/dev/null )"

    assert_contains "audition: scorecard names the candidate"   "candidate=toy-cand" "$card"
    assert_contains "audition: board size reported"             "board=2MR"          "$card"
    assert_contains "audition: total findings counted"          "findings=6"         "$card"
    assert_contains "audition: duplicates classified"           "duplicate=3"        "$card"
    assert_contains "audition: unique-verified classified"      "unique-verified=1"  "$card"
    assert_contains "audition: unique-hallucinated classified"  "unique-hallucinated=2" "$card"
    assert_contains "audition: overlap percentage"              "overlap=50%"        "$card"
    assert_contains "audition: latency field present"           "latency="           "$card"
    assert_contains "audition: cost from token counts"          "cost=\$0.0021"      "$card"

    # The scorecard must be appended to the trial ticket via a valid erg note.
    TF="$TDIR/tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg"
    if "$ERG_FIXTURE" validate "$TF" >/dev/null 2>&1 && grep -q 'audition candidate=toy-cand' "$TF"; then
        echo "PASS: audition: scorecard logged as a valid erg note"; PASS=$((PASS+1))
    else
        echo "FAIL: audition: scorecard not logged as a valid erg note"; FAIL=$((FAIL+1))
    fi

    # Idempotent roster: a second run leaves the sentinel panel.yml untouched.
    ( cd "$TDIR" && \
        REVIEWERS_FINDINGS_DIR="$FDIR" SEAT_RUNNER="$STUB" ERG="$ERG_FIXTURE" \
        REVIEWERS_PRICE_IN_PER_M=1 REVIEWERS_PRICE_OUT_PER_M=2 \
        "$REVIEWERS" audition openai/toy-candidate \
            --board "$BOARD" --endpoint http://127.0.0.1:9/v1 \
            --trial-ticket "$TRIAL" --name toy-cand ) >/dev/null 2>&1 || true
    assert_eq "audition: roster (panel.yml) never mutated" "$sentinel_before" "$(cat "$SENTINEL")"
else
    echo "SKIP: erg binary absent — audition scorecard/erg-integration tests"
fi

# ── fail-loud: an unreachable endpoint (seat-runner exits non-zero) aborts ────
DEADSTUB="$WORK/seat-dead.sh"
cat > "$DEADSTUB" <<'STUBEOF'
#!/usr/bin/env bash
echo "seat-runner: endpoint unreachable" >&2
exit 1
STUBEOF
chmod +x "$DEADSTUB"

if ( cd "$TDIR" && REVIEWERS_FINDINGS_DIR="$FDIR" SEAT_RUNNER="$DEADSTUB" ERG="$ERG_FIXTURE" \
        "$REVIEWERS" audition openai/toy-candidate --board "$BOARD" \
            --endpoint http://127.0.0.1:9/v1 --trial-ticket "$TRIAL" ) >/dev/null 2>&1; then
    echo "FAIL: audition: unreachable endpoint should exit non-zero"; FAIL=$((FAIL+1))
else
    echo "PASS: audition: unreachable endpoint exits non-zero (fail-loud)"; PASS=$((PASS+1))
fi

# ── arg validation: missing candidate model ──────────────────────────────────
if "$REVIEWERS" audition >/dev/null 2>&1; then
    echo "FAIL: audition missing model should fail"; FAIL=$((FAIL+1))
else
    echo "PASS: audition missing model fails"; PASS=$((PASS+1))
fi

# ── the shipped benchmark board parses and its anchors stay agnostic-clean ───
SHIPPED="${REPO_ROOT}/skills/reviewers/benchmark-board.yml"
if [ -f "$SHIPPED" ]; then
    # It must carry the expected ~10 board entries.
    n=$(grep -cE '^[[:space:]]*-[[:space:]]*pr:' "$SHIPPED" || true)
    if [ "$n" -ge 8 ]; then
        echo "PASS: benchmark board ships >=8 PRs ($n)"; PASS=$((PASS+1))
    else
        echo "FAIL: benchmark board ships only $n PRs (<8)"; FAIL=$((FAIL+1))
    fi
    # A smoke audition over the SHIPPED board proves it parses and runs
    # end-to-end (no real seat needed). Uses a generic stub that emits one
    # contract-shaped finding for ANY board PR (the toy stub only knows PRs 1-2).
    GENSTUB="$WORK/seat-generic.sh"
    cat > "$GENSTUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""
while [ $# -gt 0 ]; do case "$1" in --out) out="$2"; shift 2 ;; *) shift ;; esac; done
{ echo "FINDING|severity=verifiable|file=scripts/seat-runner.sh:68|rationale=generic"
  echo "SUMMARY|findings=1|verdict=revise|prompt_tokens=100|completion_tokens=20"
} > "$out"
STUBEOF
    chmod +x "$GENSTUB"
    if [ -x "$ERG_BIN" ]; then
        smoke="$( cd "$TDIR" && REVIEWERS_FINDINGS_DIR="$WORK/smoke" SEAT_RUNNER="$GENSTUB" \
            ERG="$ERG_FIXTURE" "$REVIEWERS" audition openai/toy-candidate \
                --board "$SHIPPED" --endpoint http://127.0.0.1:9/v1 \
                --trial-ticket "$TRIAL" 2>/dev/null )"
        assert_contains "shipped board: audition runs end-to-end" "audition candidate=" "$smoke"
        assert_contains "shipped board: 10-PR board size" "board=10MR" "$smoke"
    fi
else
    echo "FAIL: skills/reviewers/benchmark-board.yml missing"; FAIL=$((FAIL+1))
fi

# ── B1: seat-runner failure surfaces the .err diagnostic on stderr ───────────
# The scratch dir is reaped on exit (EXIT trap), so the error must not merely
# POINT at a now-deleted .err file — the seat-runner's own stderr has to be
# dumped to the operator's stderr before exit, or the diagnostic is unreachable.
B1ERR="$WORK/b1.stderr"
( cd "$TDIR" && REVIEWERS_FINDINGS_DIR="$FDIR" SEAT_RUNNER="$DEADSTUB" ERG="$ERG_FIXTURE" \
      "$REVIEWERS" audition openai/toy-candidate --board "$BOARD" \
          --endpoint http://127.0.0.1:9/v1 --trial-ticket "$TRIAL" ) >/dev/null 2>"$B1ERR" || true
assert_contains "audition: seat-runner failure dumps .err diagnostic to stderr" \
    "seat-runner: endpoint unreachable" "$(cat "$B1ERR")"

# ── B2: a newline in --name must not forge a second erg-log line ─────────────
# An embedded newline in --name/model would otherwise flow verbatim into the
# `erg log ... note <card>` call and inject a well-formed but forged ticket-log
# line that `erg check` cannot flag. audition must reject it (exit non-zero)
# before touching the trial ticket.
if [ -x "$ERG_BIN" ]; then
    TF2="$TDIR/tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg"
    FORGE=$'toy\n2026-01-01T00:00Z attacker note FORGED-AUDITION-LINE'
    if ( cd "$TDIR" && REVIEWERS_FINDINGS_DIR="$FDIR" SEAT_RUNNER="$STUB" ERG="$ERG_FIXTURE" \
            "$REVIEWERS" audition openai/toy-candidate --board "$BOARD" \
                --endpoint http://127.0.0.1:9/v1 --trial-ticket "$TRIAL" \
                --name "$FORGE" ) >/dev/null 2>&1; then
        echo "FAIL: audition: newline in --name should exit non-zero"; FAIL=$((FAIL+1))
    else
        echo "PASS: audition: newline in --name exits non-zero"; PASS=$((PASS+1))
    fi
    if grep -q 'FORGED-AUDITION-LINE' "$TF2"; then
        echo "FAIL: audition: newline in --name forged a ticket-log line"; FAIL=$((FAIL+1))
    else
        echo "PASS: audition: newline in --name did not forge a log line"; PASS=$((PASS+1))
    fi
fi

echo ""; echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
