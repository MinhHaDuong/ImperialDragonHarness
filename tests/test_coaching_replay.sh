#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPLAY="$ROOT/skills/coaching/replay.sh"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cat > "$WORK/board.yml" <<'YAML'
board:
  - pr: 1
    title: one
    base: deadbeef1
    head: cafebabe1
    panel: alpha.sh:10 beta.sh:*
    defects: gamma.sh:20
  - pr: 2
    title: two
    base: deadbeef2
    head: cafebabe2
    panel: delta.py:5
    defects:
YAML
cat > "$WORK/runner" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
out=; branch=; repo=; base=; model=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --out) out="$2"; shift 2;; --branch) branch="$2"; shift 2;;
        --repo) repo="$2"; shift 2;; --base) base="$2"; shift 2;;
        --model) model="$2"; shift 2;; *) shift;;
    esac
done
[[ "$repo" == "$EXPECTED_REPO" && "$model" == toy && "$out" == /*/1.findings || "$out" == /*/2.findings ]]
case "$branch" in
    cafebabe1)
        [[ "$base" == deadbeef1 ]]
        cat > "$out" <<'RESULT'
FINDING|severity=verifiable|file=src/alpha.sh:10|rationale=duplicate
FINDING|severity=verifiable|file=src/beta.sh:77|rationale=wildcard
FINDING|severity=verifiable|file=src/gamma.sh:20|rationale=confirmed
FINDING|severity=consider|file=src/zeta.sh:99|rationale=unconfirmed
SUMMARY|findings=4|verdict=revise|prompt_tokens=1000|completion_tokens=200
RESULT
        ;;
    cafebabe2)
        [[ "$base" == deadbeef2 ]]
        case "${FAIL_LATE:-}" in exit) echo 'late runner failure' >&2; exit 4;; missing) exit 0;; esac
        if [ "${CLEAN:-}" = 1 ]; then printf 'SUMMARY|findings=0|verdict=approve\n' > "$out"; exit 0; fi
        cat > "$out" <<'RESULT'
FINDING|severity=verifiable|file=lib/delta.py:5|rationale=duplicate
FINDING|severity=consider|file=lib/epsilon.py:1|rationale=unconfirmed
SUMMARY|findings=2|verdict=approve|prompt_tokens=500|completion_tokens=100
RESULT
        ;;
esac
SH
chmod +x "$WORK/runner"
mkdir -p "$WORK/repo/tickets" "$WORK/home"
printf 'sentinel\n' > "$WORK/repo/tickets/0001-test.erg"
before="$(sha256sum "$WORK/board.yml" "$WORK/repo/tickets/0001-test.erg")"
run() { HOME="$WORK/home" EXPECTED_REPO="$WORK/repo" SEAT_RUNNER="$WORK/runner" REVIEWERS_AUDITION_ELAPSED='1.0 3.0' REVIEWERS_PRICE_IN_PER_M=1 REVIEWERS_PRICE_OUT_PER_M=2 "$REPLAY" toy --repo "$WORK/repo" --board "$WORK/board.yml" --endpoint http://127.0.0.1:9/v1 "$@"; }
card="$(run)"
for field in 'board=2MR' 'findings=6' 'duplicate=3' 'unique-verified=1' 'unique-hallucinated=2' 'overlap=50%' 'latency=4.0s' 'latency-p50=1.0s' 'latency-p95=3.0s' 'cost=$0.0021'; do
    [[ "$card" == *"$field"* ]] || { echo "FAIL missing $field"; exit 1; }
done
[[ "$(sha256sum "$WORK/board.yml" "$WORK/repo/tickets/0001-test.erg")" == "$before" ]]
clean="$(CLEAN=1 run)"
[[ "$clean" == *'findings=4'* && "$clean" == *'unique-verified=1'* ]]
cat > "$WORK/empty-findings-board.yml" <<'YAML'
board:
  - pr: 2
    title: clean
    base: deadbeef2
    head: cafebabe2
    panel: delta.py:5
    defects:
YAML
zero="$(CLEAN=1 run --board "$WORK/empty-findings-board.yml")"
[[ "$zero" == *'findings=0'* && "$zero" == *'board=1MR'* ]]
for mode in exit missing; do
    if FAIL_LATE="$mode" run > "$WORK/out" 2> "$WORK/err"; then echo "FAIL: $mode accepted"; exit 1; fi
    [[ ! -s "$WORK/out" ]] || { echo "FAIL: partial success summary for $mode"; exit 1; }
    [[ -s "$WORK/err" ]] || { echo "FAIL: no diagnostic for $mode"; exit 1; }
done
if run --credential-env BAD_VAR > "$WORK/out" 2> "$WORK/err"; then echo 'FAIL: bad credential accepted'; exit 1; fi
[[ ! -s "$WORK/out" && -s "$WORK/err" ]]
[[ "$(sha256sum "$WORK/board.yml" "$WORK/repo/tickets/0001-test.erg")" == "$before" ]]
echo 'PASS: cold replay classification, diagnostics, containment, credentials and immutability'
