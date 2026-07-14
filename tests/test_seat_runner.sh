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
    # Here-string, not `printf | grep`: with `set -o pipefail`, grep -q closing
    # the pipe on an early match SIGPIPEs printf (141), which pipefail then
    # reports as the pipeline status — a nondeterministic false FAIL on a large
    # haystack. A here-string has no pipe, so no race.
    if grep -qF -- "$2" <<<"$3"; then pass "$1"; else fail "$1 (missing: $2)"; echo "  in: $3" >&2; fi
}
assert_absent() {  # label needle haystack
    if grep -qF -- "$2" <<<"$3"; then fail "$1 (found forbidden: $2)"; else pass "$1"; fi
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
# The derived venv root must be validated before it is bind-mounted: it must be
# a real venv (pyvenv.cfg) and must not be $HOME / ~/.local / an ancestor of
# $HOME. A dropped guard would let a mis-resolved aider drag the whole home in.
assert_contains "venv root validated by pyvenv.cfg"  "pyvenv.cfg"       "$CODE"
assert_contains "home-exposing mount rejected"       "_reject_home_exposing_mount" "$CODE"
# The rejection must actually cover the ancestor case, not just equality.
if printf '%s' "$CODE" | grep -Eq '\$HOMEDIR" == "\$_path"/\*|\$HOMEDIR == \$_path/\*'; then
    pass "home-exposing guard covers ancestor case"
else
    fail "home-exposing guard covers ancestor case"
fi

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
# Scoped to TRACKED files via git grep — immune to nested runtime worktrees
# and other untracked staging dirs (e.g. leftover .claude/worktrees/ siblings
# on a primary checkout) that a plain `grep -r .` would wander into.
stale="$(git -C "$REPO_ROOT" grep -l "seat-runner-prototype" \
    -- '*.sh' '*.md' '*.py' '*.yml' '*.json' \
    2>/dev/null | grep -v -e '^tickets/' -e '^tests/test_seat_runner.sh$' || true)"
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

# ── tier 2a′: home-exposing mount is refused before any podman run ───────────
# Fake an aider that resolves two levels below $HOME, so the derived venv root
# equals $HOME. With a pyvenv.cfg planted (venv check passes) the ancestor guard
# must fire and exit non-zero BEFORE run_seat ever calls `podman run`.
FH="$WORK/fakehome"; mkdir -p "$FH/bin"
: > "$FH/pyvenv.cfg"                 # make the venv check pass
printf '#!/bin/sh\n' > "$FH/bin/aider"; chmod +x "$FH/bin/aider"
STUBBIN2="$WORK/stubbin2"; mkdir -p "$STUBBIN2"
# A podman stub that FAILS if `run` is ever reached — proves the guard fires first.
cat > "$STUBBIN2/podman" <<'STUB'
#!/usr/bin/env bash
case "${1:-}" in
    run) echo "GUARD-BYPASS: podman run reached" >&2; exit 99 ;;
    *)   exit 0 ;;
esac
STUB
chmod +x "$STUBBIN2/podman"
guard_err="$(HOME="$FH" PATH="$STUBBIN2:$FH/bin:$PATH" bash "$SR" --self-test-only 2>&1 >/dev/null)" && guard_rc=0 || guard_rc=1
[ "$guard_rc" -ne 0 ] && pass "home-exposing venv root exits non-zero" || fail "home-exposing venv root exits non-zero"
assert_contains "guard names the refused mount"      "refusing to mount" "$guard_err"
assert_absent   "guard fires before any podman run"  "GUARD-BYPASS"      "$guard_err"

# ── tier 1b: new-flag source assertions ──────────────────────────────────────
# The two new flags must be handled in the arg parser (a case arm each).
assert_contains "--credential-env flag parsed"       "--credential-env" "$SRC"
assert_contains "--health-path flag parsed"          "--health-path"    "$SRC"
# The https branch maps the real hostname to loopback via --add-host so the
# client still presents valid SNI/cert while the traffic is bridged.
assert_contains "https branch adds --add-host"       "--add-host"       "$SRC"
# The in-container bridge port must be one variable used consistently: in the
# CONTAINER_BASE the client dials, AND in the container-side relay listen/wait.
assert_contains "in-container port var in CONTAINER_BASE" 'CONTAINER_PORT}${ENDPOINT_PATH}' "$CODE"
if printf '%s' "$CODE" | grep -Eq 'net-relay.py --listen tcp:127.0.0.1:\$\{CONTAINER_PORT\}'; then
    pass "in-container port var drives the bridge listen"
else
    fail "in-container port var drives the bridge listen"
fi
# The secret must NEVER be inlined into podman argv (ps -ef leak). The live code
# builds the BARE `-e OPENAI_API_KEY` passthrough when a credential is set, so
# podman reads the value from the process env instead of argv.
assert_contains "credential passed as bare -e passthrough" "CRED_ARGS=(-e OPENAI_API_KEY)" "$CODE"

# ── tier 2a″: --credential-env moves the secret via ENV, never argv ──────────
# RED before this feature: seat-runner rejects --credential-env as an unknown
# arg and exits 2 without ever invoking podman. Stub podman captures its argv
# and the environment it was launched with.
if command -v python3 >/dev/null; then
    STUBBIN3="$WORK/stubbin3"; mkdir -p "$STUBBIN3"
    cat > "$STUBBIN3/podman" <<'STUB'
#!/usr/bin/env bash
case "${1:-}" in
    run)
        [ -n "${PODMAN_ARGV_CAP:-}" ] && printf '%s\n' "$@" > "$PODMAN_ARGV_CAP"
        [ -n "${PODMAN_ENV_CAP:-}"  ] && env         > "$PODMAN_ENV_CAP"
        ;;
esac
exit 0
STUB
    chmod +x "$STUBBIN3/podman"

    PROBE_VAL="probe-${RANDOM}-${RANDOM}"
    ARGV_CAP="$WORK/cred.argv"; ENV_CAP="$WORK/cred.env"
    MY_TEST_VAR="$PROBE_VAL" PODMAN_ARGV_CAP="$ARGV_CAP" PODMAN_ENV_CAP="$ENV_CAP" \
        PATH="$STUBBIN3:$PATH" bash "$SR" --self-test-only --credential-env MY_TEST_VAR \
        >/dev/null 2>&1 || true
    if [ -f "$ARGV_CAP" ] && [ -f "$ENV_CAP" ]; then
        # The secret reaches the container through the process env podman inherits...
        assert_contains "credential-env: secret reaches podman via process env" \
            "OPENAI_API_KEY=${PROBE_VAL}" "$(cat "$ENV_CAP")"
        # ...as a BARE -e passthrough in argv (a line that is exactly the var name)...
        if grep -qx 'OPENAI_API_KEY' "$ARGV_CAP"; then
            pass "credential-env: argv carries bare -e OPENAI_API_KEY passthrough"
        else
            fail "credential-env: argv carries bare -e OPENAI_API_KEY passthrough"
        fi
        # ...and the VALUE must NEVER appear in argv (that is the ps -ef leak).
        if grep -qF "OPENAI_API_KEY=${PROBE_VAL}" "$ARGV_CAP"; then
            fail "credential-env: SECRET LEAKED into podman argv (ps -ef visible)"
        else
            pass "credential-env: secret absent from podman argv (no ps -ef leak)"
        fi
    else
        fail "credential-env: podman never invoked (arg rejected?)"
    fi

    # ── https branch: --add-host + 8443 CONTAINER_BASE reach the podman run ──
    HTTPS_ARGV="$WORK/https.argv"
    PODMAN_ARGV_CAP="$HTTPS_ARGV" PATH="$STUBBIN3:$PATH" \
        bash "$SR" --self-test-only --endpoint https://openrouter.ai/api/v1 \
        >/dev/null 2>&1 || true
    https_argv="$(cat "$HTTPS_ARGV" 2>/dev/null || true)"
    assert_contains "https: --add-host maps real host to loopback" \
        "openrouter.ai:127.0.0.1" "$https_argv"
    assert_contains "https: container base = scheme + real host + 8443 + path" \
        "https://openrouter.ai:8443/api/v1" "$https_argv"

    # ── http branch: byte-identical to v1 (no --add-host, same host:port) ────
    HTTP_ARGV="$WORK/http.argv"
    PODMAN_ARGV_CAP="$HTTP_ARGV" PATH="$STUBBIN3:$PATH" \
        bash "$SR" --self-test-only --endpoint http://127.0.0.1:8012/v1 \
        >/dev/null 2>&1 || true
    http_argv="$(cat "$HTTP_ARGV" 2>/dev/null || true)"
    assert_absent   "http: no --add-host on a plain-http endpoint" "add-host" "$http_argv"
    assert_contains "http: container base unchanged (byte-identical)" \
        "http://127.0.0.1:8012/v1" "$http_argv"
else
    echo "SKIP: python3 absent — credential-env / add-host argv tests"
fi

# ── tier 2a‴: health-path URL is built from the origin (no double-/api) ───────
# The probe URL must be SCHEME://AUTHORITY + --health-path, NOT ${ENDPOINT%/v1}
# + path (which double-prefixes /api for an /api/v1 endpoint). Stub curl to
# capture the URL and fail so seat-runner stops right at the probe.
CURLBIN="$WORK/curlbin"; mkdir -p "$CURLBIN"
cat > "$CURLBIN/curl" <<'STUB'
#!/usr/bin/env bash
for a in "$@"; do url="$a"; done          # the URL is the last argument
[ -n "${CURL_URL_CAP:-}" ] && printf '%s\n' "$url" > "$CURL_URL_CAP"
exit 22                                    # "unreachable" → seat-runner stops here
STUB
chmod +x "$CURLBIN/curl"
URL_CAP="$WORK/curl.url"
CURL_URL_CAP="$URL_CAP" PATH="$CURLBIN:${STUBBIN3:-$WORK/stubbin3}:$PATH" \
    bash "$SR" --endpoint https://openrouter.ai/api/v1 --health-path /api/v1/models \
    --branch dummy >/dev/null 2>&1 || true
probe_url="$(cat "$URL_CAP" 2>/dev/null || true)"
assert_contains "health-path: exact URL built from origin" \
    "https://openrouter.ai/api/v1/models" "$probe_url"
assert_absent   "health-path: no double-/api prefix" "api/api" "$probe_url"

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
