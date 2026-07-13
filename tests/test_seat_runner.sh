#!/usr/bin/env bash
# Tests for scripts/seat-runner.sh — the ticket-0217 OS-contained reviewer seat.
#
# Two tiers, both in one suite (test_bash_suites.py runs it as one integration
# subprocess, 120s budget):
#   1. source-inspection checks (no podman) — flag presence, the network-deny
#      posture (--network=none present, --network=host absent), the timeout
#      wrapper, and that the relay/Containerfile artifacts exist. These catch a
#      reintroduced --network=host or a dropped timeout cheaply.
#   2. behavioural checks — a real containment self-test (podman + the
#      localhost/seat-runner:v1 image; SKIP when either is absent, never build
#      the image here) and a timeout test that stubs podman (needs neither).
#
# SKIP convention mirrors tests/test_reviewers.sh: echo "SKIP: reason" and keep
# going; a genuine defect FAILs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SR="${REPO_ROOT}/scripts/seat-runner.sh"
RELAY="${REPO_ROOT}/scripts/seat-runner/net-relay.py"
CONTAINERFILE="${REPO_ROOT}/scripts/seat-runner/Containerfile"
IMAGE="localhost/seat-runner:v1"
PASS=0; FAIL=0
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

pass() { echo "PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL+1)); }
assert_contains() {  # label needle haystack
    if printf '%s' "$3" | grep -qF -- "$2"; then pass "$1"; else fail "$1 (missing: $2)"; echo "  in: $3" >&2; fi
}
assert_absent() {  # label needle haystack
    if printf '%s' "$3" | grep -qF -- "$2"; then fail "$1 (found forbidden: $2)"; else pass "$1"; fi
}

# ── tier 1: source inspection (no podman needed) ─────────────────────────────
[ -f "$SR" ] || { echo "FAIL: scripts/seat-runner.sh missing (rename not done)"; echo "Results: 0 passed, 1 failed"; exit 1; }
SRC="$(cat "$SR")"

assert_contains "self-test-only flag exists"        "--self-test-only" "$SRC"
assert_contains "network deny-by-default present"   "--network=none"   "$SRC"
# Only LIVE code counts: the header comment names the retired --network=host on
# purpose. Strip comment lines before asserting the flag is gone.
CODE="$(printf '%s\n' "$SRC" | grep -v '^[[:space:]]*#')"
assert_absent   "no --network=host in live code"    "--network=host"   "$CODE"
assert_contains "per-seat timeout env honoured"     "SEAT_TIMEOUT"     "$SRC"
# The timeout must actually WRAP the container invocation, not merely be read.
if printf '%s' "$SRC" | grep -Eq 'timeout[^|]*"?\$\{?SEAT_TIMEOUT'; then
    pass "timeout wraps the seat invocation"
else
    fail "timeout wraps the seat invocation"
fi
assert_contains "relay bind-mounted into container"  "relay.sock"      "$SRC"
# timeout SIGKILLs only the podman client (rootless conmon keeps the container
# alive), so the seat must be --name'd and force-reaped or it leaks/outlives.
assert_contains "container is named for reaping"     "--name"          "$SRC"
assert_contains "orphaned container is force-reaped"  "podman rm -f"    "$SRC"
# ~/.local must NOT be wholesale-mounted (it holds keyrings/wallets/tokens);
# only the allowlisted CLI venv + interpreter are exposed.
assert_absent   "no wholesale ~/.local mount"        'HOMEDIR/.local"'  "$CODE"
assert_contains "allowlisted code-only mounts"       "SEAT_CODE_MOUNTS" "$SRC"
assert_contains "self-test proves ~/.local scoped"   "LOCAL-SCOPED"     "$SRC"

[ -f "$RELAY" ] && pass "net-relay.py exists" || fail "net-relay.py exists"
if command -v python3 >/dev/null; then
    if python3 -c "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)" "$RELAY" 2>/dev/null; then
        pass "net-relay.py compiles"
    else
        fail "net-relay.py compiles"
    fi
fi
[ -f "$CONTAINERFILE" ] && pass "Containerfile exists" || fail "Containerfile exists"

# ── reference sweep: the old prototype name is gone outside tickets/ ──────────
# This suite mentions the old name in its own sweep pattern; exclude it and the
# append-only ticket history (which keeps the historical name deliberately).
stale="$(cd "$REPO_ROOT" && grep -rl "seat-runner-prototype" \
    --include='*.sh' --include='*.md' --include='*.py' --include='*.yml' --include='*.json' . \
    2>/dev/null | grep -v -e '^\./tickets/' -e 'tests/test_seat_runner.sh' || true)"
if [ -z "$stale" ]; then pass "no seat-runner-prototype refs outside tickets/"; else fail "stale seat-runner-prototype refs: $stale"; fi

# ── tier 2a: timeout behaviour (stubbed podman; no image needed) ─────────────
if command -v python3 >/dev/null && command -v timeout >/dev/null; then
    STUBBIN="$WORK/stubbin"; mkdir -p "$STUBBIN"
    cat > "$STUBBIN/podman" <<'STUB'
#!/usr/bin/env bash
# Only `podman run` hangs (a seat far past SEAT_TIMEOUT); everything else
# (image-exists probes, the rm -f reaping call) returns immediately so the
# measured wall-clock reflects the timeout, not the stub.
case "${1:-}" in
    run) sleep 30 ;;
    *)   exit 0 ;;
esac
STUB
    chmod +x "$STUBBIN/podman"
    start=$SECONDS
    if PATH="$STUBBIN:$PATH" SEAT_TIMEOUT=2 bash "$SR" --self-test-only >/dev/null 2>&1; then
        rc=0; else rc=1; fi
    elapsed=$((SECONDS - start))
    # A hung seat must exit non-zero...
    [ "$rc" -ne 0 ] && pass "timeout: hung seat exits non-zero" || fail "timeout: hung seat exits non-zero"
    # ...and be KILLED near SEAT_TIMEOUT, not run the full 30s (proves the wrap).
    if [ "$elapsed" -lt 15 ]; then pass "timeout: bounded wall-clock (${elapsed}s < 15s)"; else fail "timeout: seat ran ${elapsed}s — timeout not enforced"; fi
else
    echo "SKIP: python3/timeout absent — timeout behaviour test"
fi

# ── tier 2b: real containment self-test (podman + image) ─────────────────────
if ! command -v podman >/dev/null; then
    echo "SKIP: podman absent — containment self-test"
elif ! podman image exists "$IMAGE" 2>/dev/null; then
    echo "SKIP: image ${IMAGE} absent — containment self-test (build out of band)"
else
    st_err="$(bash "$SR" --self-test-only 2>&1 >/dev/null)" && st_rc=0 || st_rc=1
    [ "$st_rc" -eq 0 ] && pass "self-test-only exits 0" || { fail "self-test-only exits 0"; echo "$st_err" >&2; }
    assert_contains "self-test reports containment OK" "containment OK" "$st_err"

    # Network-deny regression: an external host must be UNREACHABLE from inside
    # the sandbox. The self-test's own probe proves it; assert the OK line
    # states external network is denied. A reintroduced --network=host would
    # make the probe reach the host and this FAIL.
    assert_contains "self-test proves external network denied" "network denied" "$st_err"
    # Secret-exposure regression guard: the banner asserts ~/.local is scoped to
    # the CLI venv. A wholesale ~/.local mount would flip the probe to
    # LOCAL-OVERMOUNTED and fail the self-test before this banner prints.
    assert_contains "self-test proves ~/.local scoped" "scoped to CLI venv" "$st_err"
fi

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
