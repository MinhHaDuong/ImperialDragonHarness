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

# --- hermetic credential scope (2026-07-27) ----------------------------------
# Every credential this suite handles is a FIXTURE, injected via
# --credential-env MY_TEST_VAR; seat-runner re-exports that fixture value as
# OPENAI_API_KEY for its children, which is why the exfiltration stubs below
# interpolate "${OPENAI_API_KEY:-}" — they are meant to echo the fixture, and
# the assertions check the scrub removed it.
#
# That only holds if no REAL key is in scope. When the injection does not reach
# a stub, the stub inherits the ambient environment instead, and a failing
# assertion prints whatever it found. On 2026-07-27 that spilled a live
# OpenAI key into a terminal and a session transcript.
#
# So: drop every provider credential before anything runs. A stub that misses
# the injection now prints an empty string, not a secret.
unset OPENAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY DEEPSEEK_API_KEY \
      MISTRAL_API_KEY TAVILY_API_KEY ZOTERO_API_KEY ZOTERO_RW_API_KEY

# Unsetting here is NOT enough on its own. BASH_ENV points every child bash at
# scripts/bash-env.sh, which re-runs the KEYS selection and re-exports the real
# credential — overriding whatever this parent set. The stubs are bash scripts,
# so they were being handed the live key no matter what happened up here. Clear
# BASH_ENV so children stay hermetic; the fixture arrives via --credential-env,
# which needs no loader.
export BASH_ENV=

# Assert against a CHILD, not this shell. A parent-scope check passes while the
# leak is alive, because re-injection happens on child startup — that blind spot
# is what made the first attempt at this fix a no-op.
_hermetic_probe="$(bash -c 'printf "%s" "${OPENAI_API_KEY:-}"')"
if [ -n "$_hermetic_probe" ]; then
    printf 'FAIL: child processes still receive a credential; suite is not hermetic\n' >&2
    exit 1
fi
unset _hermetic_probe

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
    # Pure-bash substring match, no subprocess: the quoted needle makes `==`
    # a literal (glob-free) comparison, identical to `grep -F`. This supersedes
    # the earlier here-string form (`grep -qF <<<`): a per-call grep subprocess
    # reading a here-string tmpfile proved to intermittently return no-match
    # under parallel `make check` load while the haystack was provably intact
    # (ticket 0329). The bash builtin has neither a pipe nor a tmpfile, so
    # neither the SIGPIPE race nor the under-load flake can occur.
    if [[ "$3" == *"$2"* ]]; then pass "$1"; else fail "$1 (missing: $2)"; echo "  in: $3" >&2; fi
}
assert_absent() {  # label needle haystack
    if [[ "$3" == *"$2"* ]]; then fail "$1 (found forbidden: $2)"; else pass "$1"; fi
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
if grep -Eq 'timeout[^|]*"?\$\{?SEAT_TIMEOUT' <<<"$SRC"; then
    pass "timeout wraps the seat invocation"
else
    fail "timeout wraps the seat invocation"
fi
# The aider/litellm per-request timeout backstop (ticket 0347): the env knob is
# documented AND the aider invocation actually passes --timeout, so a silent
# litellm hang becomes a stderr exception instead of a SEAT_TIMEOUT SIGKILL.
assert_contains "aider timeout backstop env documented" "AIDER_API_TIMEOUT" "$SRC"
if grep -Eq 'timeout "\$\{AIDER_API_TIMEOUT' <<<"$SRC"; then
    pass "aider invocation passes --timeout backstop"
else
    fail "aider invocation passes --timeout backstop"
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
if grep -Eq '\$HOMEDIR" == "\$_path"/\*|\$HOMEDIR == \$_path/\*' <<<"$CODE"; then
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
if grep -Eq 'net-relay.py --listen tcp:127.0.0.1:\$\{CONTAINER_PORT\}' <<<"$CODE"; then
    pass "in-container port var drives the bridge listen"
else
    fail "in-container port var drives the bridge listen"
fi
# The secret must NEVER be inlined into podman argv (ps -ef leak). The live code
# builds the BARE `-e OPENAI_API_KEY` passthrough when a credential is set, so
# podman reads the value from the process env instead of argv.
assert_contains "credential passed as bare -e passthrough" "CRED_ARGS=(-e OPENAI_API_KEY)" "$CODE"

# ── tier 1c: egress is pinned to the single ENDPOINT pair (0207 mitigation b) ──
# The host-side relay must construct exactly ONE outbound target, and it must be
# the ENDPOINT host:port pair — no wildcard, no second destination. A seat under
# --network=none reaches only this relay, so a second or all-hosts target would
# widen the egress a prompt-injected seat could exfiltrate through.
host_connects="$(grep -Fc -- '--connect "tcp:${ENDPOINT_HOST}:${ENDPOINT_PORT}"' "$SR" || true)"
if [ "$host_connects" = "1" ]; then
    pass "egress: exactly one host-side relay target (the ENDPOINT pair)"
else
    fail "egress: expected 1 host-side ENDPOINT relay target, found ${host_connects}"
fi
assert_absent "egress: no all-interfaces relay destination"  'tcp:0.0.0.0' "$CODE"
assert_absent "egress: no wildcard relay destination"        'tcp:*:'      "$CODE"

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
        # ...but NOT into the containment self-test container: that run is invoked
        # with `run_seat --no-cred` (ticket 0339, least-privilege), so the endpoint
        # key must be ABSENT from the self-test argv (this is the only podman run
        # under --self-test-only). The ENV_CAP assertion above is unaffected: the
        # runner unconditionally exports OPENAI_API_KEY into its OWN process env at
        # credential setup, which the stub inherits regardless of the -e argv the
        # container receives — so env-inheritance can't discriminate; argv can.
        if grep -qx 'OPENAI_API_KEY' "$ARGV_CAP"; then
            fail "credential-env: self-test container carries the endpoint key (--no-cred not applied)"
        else
            pass "credential-env: self-test container omits the endpoint key (--no-cred, ticket 0339)"
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

# ── tier 2a⁗: credential scrub — an exfiltrated key never leaves the seat ─────
# 0207 red-team (mitigation a): the reviewer reads attacker-controllable diff
# text and its output flows back out, so a prompt-injected diff could coax the
# injected key into the findings/stderr channels. Stub podman to MODEL that leak:
# the containment probe emits its markers; the review run "leaks" the credential
# it was handed (OPENAI_API_KEY, inherited from the process env) into its output.
# When --credential-env carries a real secret, seat-runner must redact it from
# BOTH the findings file (grep→$OUT path) AND anything echoed to stderr (the
# failure-tail path) BEFORE those paths read the captures. The credential is a
# random dummy string here — never a real key.
if command -v python3 >/dev/null && command -v git >/dev/null && command -v aider >/dev/null; then
    # A throwaway repo with a one-line main→feature diff (the review path needs a
    # non-empty diff; seat-runner clones $REPO and diffs origin/main...feature).
    EXFIL_REPO="$WORK/exfilrepo"
    mkdir -p "$EXFIL_REPO"
    (
        cd "$EXFIL_REPO"
        git init -q -b main
        git config user.email t@t; git config user.name t
        printf 'line one\n' > f.txt
        git add f.txt; git commit -qm base
        git checkout -q -b feature
        printf 'line one\nline two\n' > f.txt
        git commit -qam change
    )
    # podman stub: the self-test probe carries SANDBOX-ALIVE → emit containment
    # markers; the review run carries none → "leak" the injected key into a
    # FINDING line (stdout→raw.out) AND to stderr (raw.err), so BOTH scrub paths
    # are exercised. The key is read from the stub's own env — exactly how a
    # compromised seat would obtain it.
    # This stub also captures per-branch argv (self-test vs review) so the test
    # can prove least-privilege credential scoping (ticket 0339): the self-test
    # container must NOT receive the endpoint key, the review run must.
    EXFILBIN="$WORK/exfilbin"; mkdir -p "$EXFILBIN"
    cat > "$EXFILBIN/podman" <<'STUB'
#!/usr/bin/env bash
if [ "${1:-}" = run ]; then
    if printf '%s\n' "$@" | grep -q SANDBOX-ALIVE; then
        [ -n "${PODMAN_SELFTEST_ARGV_CAP:-}" ] && printf '%s\n' "$@" > "$PODMAN_SELFTEST_ARGV_CAP"
        printf 'SANDBOX-ALIVE\nWRITE-BLOCKED\nSECRET-BLOCKED\nLOCAL-SCOPED\nNET-BLOCKED\n'
    else
        [ -n "${PODMAN_REVIEW_ARGV_CAP:-}" ] && printf '%s\n' "$@" > "$PODMAN_REVIEW_ARGV_CAP"
        printf 'FINDING|severity=verifiable|file=f.txt:1|rationale=leaked %s\n' "${OPENAI_API_KEY:-}"
        printf 'SUMMARY|findings=1|verdict=revise\n'
        printf 'leaked %s\n' "${OPENAI_API_KEY:-}" >&2
    fi
fi
exit 0
STUB
    chmod +x "$EXFILBIN/podman"

    PROBE_VAL="exfil-secret-${RANDOM}-${RANDOM}-${RANDOM}"
    FINDINGS="$WORK/exfil.findings"
    SELFTEST_ARGV="$WORK/exfil.selftest.argv"; REVIEW_ARGV="$WORK/exfil.review.argv"

    # Success path: findings file is written from raw.out; assert it is scrubbed.
    MY_TEST_VAR="$PROBE_VAL" PATH="$EXFILBIN:$PATH" \
        PODMAN_SELFTEST_ARGV_CAP="$SELFTEST_ARGV" PODMAN_REVIEW_ARGV_CAP="$REVIEW_ARGV" \
        bash "$SR" --repo "$EXFIL_REPO" --base origin/main --branch feature \
        --endpoint http://127.0.0.1:9/v1 --health-path "" \
        --credential-env MY_TEST_VAR --out "$FINDINGS" \
        >/dev/null 2>"$WORK/exfil.stderr.ok" || true
    findings_out="$(cat "$FINDINGS" 2>/dev/null || true)"
    assert_absent   "scrub: injected key absent from findings file" "$PROBE_VAL" "$findings_out"
    assert_contains "scrub: findings carry the redaction marker" "[REDACTED-CREDENTIAL]" "$findings_out"

    # ── 0339 least-privilege: the self-test container omits the endpoint key,
    # the review run keeps it. Argv is the ONLY discriminating channel — the
    # runner exports OPENAI_API_KEY into its process env, which BOTH stub runs
    # inherit regardless of the -e flags, so an env-dump check would be a
    # tautology (passes before AND after the fix). The bare `-e OPENAI_API_KEY`
    # passthrough puts the var name on its own argv line. The review-run guard is
    # green before and after the fix — it catches a blanket-strip wrong fix.
    if [ -f "$SELFTEST_ARGV" ] && grep -qx 'OPENAI_API_KEY' "$SELFTEST_ARGV"; then
        fail "no-cred: self-test container carries the endpoint key (should be stripped)"
    else
        pass "no-cred: self-test container omits the endpoint key (ticket 0339)"
    fi
    if [ -f "$REVIEW_ARGV" ] && grep -qx 'OPENAI_API_KEY' "$REVIEW_ARGV"; then
        pass "no-cred: review run still carries the endpoint key (invariant)"
    else
        fail "no-cred: review run lost the endpoint key (over-strip regression?)"
    fi

    # Failure path: a seat that exits non-zero has raw.err tailed to stderr. A
    # second stub leaks the key to stderr, then exits 1 to drive that tail path.
    EXFILBIN2="$WORK/exfilbin2"; mkdir -p "$EXFILBIN2"
    cat > "$EXFILBIN2/podman" <<'STUB'
#!/usr/bin/env bash
if [ "${1:-}" = run ]; then
    if printf '%s\n' "$@" | grep -q SANDBOX-ALIVE; then
        printf 'SANDBOX-ALIVE\nWRITE-BLOCKED\nSECRET-BLOCKED\nLOCAL-SCOPED\nNET-BLOCKED\n'
        exit 0
    fi
    printf 'aider crashed after leaking %s\n' "${OPENAI_API_KEY:-}" >&2
    exit 1
fi
exit 0
STUB
    chmod +x "$EXFILBIN2/podman"
    exfil_stderr="$(MY_TEST_VAR="$PROBE_VAL" PATH="$EXFILBIN2:$PATH" \
        bash "$SR" --repo "$EXFIL_REPO" --base origin/main --branch feature \
        --endpoint http://127.0.0.1:9/v1 --health-path "" \
        --credential-env MY_TEST_VAR --out "$WORK/exfil.findings2" 2>&1 >/dev/null || true)"
    assert_absent   "scrub: injected key absent from failure-path stderr" "$PROBE_VAL" "$exfil_stderr"
    assert_contains "scrub: failure-path stderr carries the redaction marker" "[REDACTED-CREDENTIAL]" "$exfil_stderr"

    # WARN-cat path: a seat that EXITS ZERO but emits NO contract-shaped line
    # makes the contract-grep fail, so seat-runner cats raw.out to stderr and
    # exits 1. A third stub leaks the key into that non-contract stdout to prove
    # the scrub covers this echo path too (the third of the three the fix claims).
    EXFILBIN3="$WORK/exfilbin3"; mkdir -p "$EXFILBIN3"
    cat > "$EXFILBIN3/podman" <<'STUB'
#!/usr/bin/env bash
if [ "${1:-}" = run ]; then
    if printf '%s\n' "$@" | grep -q SANDBOX-ALIVE; then
        printf 'SANDBOX-ALIVE\nWRITE-BLOCKED\nSECRET-BLOCKED\nLOCAL-SCOPED\nNET-BLOCKED\n'
    else
        # No FINDING|/SUMMARY| line → contract-grep fails → WARN cat raw.out.
        printf 'aider babble, no contract lines, key was %s\n' "${OPENAI_API_KEY:-}"
    fi
fi
exit 0
STUB
    chmod +x "$EXFILBIN3/podman"
    warn_stderr="$(MY_TEST_VAR="$PROBE_VAL" PATH="$EXFILBIN3:$PATH" \
        bash "$SR" --repo "$EXFIL_REPO" --base origin/main --branch feature \
        --endpoint http://127.0.0.1:9/v1 --health-path "" \
        --credential-env MY_TEST_VAR --out "$WORK/exfil.findings3" 2>&1 >/dev/null || true)"
    assert_absent   "scrub: injected key absent from WARN-cat stderr" "$PROBE_VAL" "$warn_stderr"
    assert_contains "scrub: WARN-cat stderr carries the redaction marker" "[REDACTED-CREDENTIAL]" "$warn_stderr"
else
    echo "SKIP: python3/git/aider absent — credential-scrub exfiltration test"
fi

# ── tier 2a⁶: reasoning-shape pre-flight probe (ticket 0347) ─────────────────
# z-ai/glm-5.2 and moonshotai/kimi-k2.7-code return a `reasoning` /
# `reasoning_content` field alongside `content`; the seat's pinned aider/litellm
# venv hangs on that shape and the outer SEAT_TIMEOUT SIGKILL leaves EMPTY stderr
# — a silent timeout. seat-runner must probe the endpoint host-side (max_tokens=1)
# BEFORE any container launch and fail LOUD when the response carries a non-empty
# reasoning field. --health-path "" skips the health probe so every curl call here
# is the reasoning probe; --credential-env activates it. The RED (blocking) cases
# FATAL at the probe BEFORE aider resolution or any clone, so they need neither
# aider nor a git repo — they run in the merge gate (python3 only), where the
# real-container tier below SKIPs. Only the negative-space case needs the full
# review path (aider + repo) to reach podman run.
if command -v python3 >/dev/null; then
    # _reasoning_probe_red MODEL BODY_JSON LABEL — stub the probe endpoint (curl)
    # to return BODY_JSON and stub podman to scream if `run` is reached; assert
    # seat-runner exits non-zero, names the hang class, and never reaches podman.
    _reasoning_probe_red() {
        local model="$1" body="$2" label="$3"
        local bin; bin="$(mktemp -d "$WORK/rsnred.XXXXXX")"
        cat > "$bin/curl" <<'STUB'
#!/usr/bin/env bash
printf '%s' "$PROBE_BODY_JSON"      # the reasoning-shape probe response
exit 0
STUB
        cat > "$bin/podman" <<'STUB'
#!/usr/bin/env bash
case "${1:-}" in
    run) echo "GUARD-BYPASS: podman run reached" >&2; exit 99 ;;
    *)   exit 0 ;;
esac
STUB
        chmod +x "$bin/curl" "$bin/podman"
        local err rc=0
        err="$(PROBE_BODY_JSON="$body" MY_TEST_VAR="probe-key-${RANDOM}" PATH="$bin:$PATH" \
            bash "$SR" --base origin/main --branch feature \
            --model "$model" --endpoint http://127.0.0.1:9/v1 --health-path "" \
            --credential-env MY_TEST_VAR --out "$bin/out" 2>&1 >/dev/null)" || rc=1
        [ "$rc" -ne 0 ] && pass "reasoning-probe: ${label} exits non-zero" \
            || fail "reasoning-probe: ${label} exits non-zero"
        assert_contains "reasoning-probe: ${label} names the hang class"        "reasoning-field response" "$err"
        assert_absent   "reasoning-probe: ${label} blocks before any podman run" "GUARD-BYPASS"            "$err"
    }
    # glm-5.2 shape: `reasoning`. kimi-k2.7-code shape: `reasoning_content`.
    # Both must block — pins both halves of the ticket's reasoning-response canary.
    _reasoning_probe_red "openai/z-ai/glm-5.2" \
        '{"choices":[{"message":{"content":"ok","reasoning":"let me think about it"}}]}' \
        "reasoning field (glm-5.2)"
    _reasoning_probe_red "openai/moonshotai/kimi-k2.7-code" \
        '{"choices":[{"message":{"content":"ok","reasoning_content":"step-by-step"}}]}' \
        "reasoning_content field (kimi-k2.7-code)"

    # Negative-space case: an ordinary (content-only) body must NOT block — the
    # full review path reaches podman run. Guards against a tautological always-
    # block. This one needs aider + a real diff (the review path clones + diffs).
    if command -v git >/dev/null && command -v aider >/dev/null; then
        RSN_REPO="$WORK/rsnrepo"; mkdir -p "$RSN_REPO"
        (
            cd "$RSN_REPO"
            git init -q -b main
            git config user.email t@t; git config user.name t
            printf 'line one\n' > f.txt
            git add f.txt; git commit -qm base
            git checkout -q -b feature
            printf 'line one\nline two\n' > f.txt
            git commit -qam change
        )
        RSNBIN2="$WORK/rsnbin2"; mkdir -p "$RSNBIN2"
        cat > "$RSNBIN2/curl" <<'STUB'
#!/usr/bin/env bash
printf '{"choices":[{"message":{"content":"ok"}}]}'
exit 0
STUB
        chmod +x "$RSNBIN2/curl"
        cat > "$RSNBIN2/podman" <<'STUB'
#!/usr/bin/env bash
if [ "${1:-}" = run ]; then
    : > "${PODMAN_RUN_MARKER:-/dev/null}"          # prove run was reached
    if printf '%s\n' "$@" | grep -q SANDBOX-ALIVE; then
        printf 'SANDBOX-ALIVE\nWRITE-BLOCKED\nSECRET-BLOCKED\nLOCAL-SCOPED\nNET-BLOCKED\n'
    else
        printf 'SUMMARY|findings=0|verdict=approve\n'
    fi
fi
exit 0
STUB
        chmod +x "$RSNBIN2/podman"
        RUN_MARKER="$WORK/rsn.runmarker"
        PODMAN_RUN_MARKER="$RUN_MARKER" MY_TEST_VAR="probe-key-${RANDOM}" PATH="$RSNBIN2:$PATH" \
            bash "$SR" --repo "$RSN_REPO" --base origin/main --branch feature \
            --model openai/devstral-small-2 --endpoint http://127.0.0.1:9/v1 --health-path "" \
            --credential-env MY_TEST_VAR --out "$WORK/rsn.out2" >/dev/null 2>&1 || true
        [ -f "$RUN_MARKER" ] && pass "reasoning-probe: ordinary model reaches podman run (no false block)" \
            || fail "reasoning-probe: ordinary model reaches podman run (no false block)"
    else
        echo "SKIP: git/aider absent — reasoning-probe negative-space case"
    fi

    # Test A (item 1): a parser verdict OUTSIDE {0,1,2} — e.g. python3 killed,
    # exit 42 — must fail LOUD, not silently proceed as "safe". Dispatch python3
    # on the -c script: the body builder (json.dumps) works; the response parser
    # (json.load) exits 42. The probe is advisory, so the run proceeds — but a
    # WARN naming the unexpected verdict code must be emitted (fail-open, LOUD).
    _rp_realpy="$(command -v python3)"
    _rpA="$(mktemp -d "$WORK/rpA.XXXXXX")"
    cat > "$_rpA/curl" <<'STUB'
#!/usr/bin/env bash
printf '{"choices":[{"message":{"content":"ok"}}]}'
exit 0
STUB
    printf '%s\n' "$_rp_realpy" > "$_rpA/realpy"
    cat > "$_rpA/python3" <<'STUB'
#!/usr/bin/env bash
script=""; [ "${1:-}" = "-c" ] && script="${2:-}"
case "$script" in
    *json.load*)  exit 42 ;;                                              # response parser → unexpected verdict
    *json.dumps*) printf '{"model":"x","max_tokens":1,"messages":[]}'; exit 0 ;;
    *) exec "$(cat "$(dirname "$0")/realpy")" "$@" ;;
esac
STUB
    chmod +x "$_rpA/curl" "$_rpA/python3"
    errA="$(MY_TEST_VAR="probe-key-${RANDOM}" PATH="$_rpA:$PATH" \
        bash "$SR" --base origin/main --branch feature \
        --model openai/devstral-small-2 --endpoint http://127.0.0.1:9/v1 --health-path "" \
        --credential-env MY_TEST_VAR --out "$_rpA/out" 2>&1 >/dev/null || true)"
    assert_contains "reasoning-probe: unexpected verdict code warns loud (not silent-safe)" \
        "unexpected verdict code" "$errA"

    # Test B (item 2): if the request-body builder (python3 json.dumps) crashes,
    # the unguarded command substitution used to abort the ENTIRE seat run under
    # set -euo pipefail. The probe is advisory: a body-build failure must WARN
    # and fall through to the normal run, not kill the seat for every model.
    _rpB="$(mktemp -d "$WORK/rpB.XXXXXX")"
    cat > "$_rpB/curl" <<'STUB'
#!/usr/bin/env bash
printf '{"choices":[{"message":{"content":"ok"}}]}'
exit 0
STUB
    cat > "$_rpB/python3" <<'STUB'
#!/usr/bin/env bash
script=""; [ "${1:-}" = "-c" ] && script="${2:-}"
case "$script" in
    *json.dumps*) echo "boom" >&2; exit 7 ;;                             # body builder crashes
    *) exit 2 ;;
esac
STUB
    chmod +x "$_rpB/curl" "$_rpB/python3"
    errB="$(MY_TEST_VAR="probe-key-${RANDOM}" PATH="$_rpB:$PATH" \
        bash "$SR" --base origin/main --branch feature \
        --model openai/devstral-small-2 --endpoint http://127.0.0.1:9/v1 --health-path "" \
        --credential-env MY_TEST_VAR --out "$_rpB/out" 2>&1 >/dev/null || true)"
    assert_contains "reasoning-probe: body-build failure warns and does not abort the seat" \
        "could not build its request body" "$errB"
else
    echo "SKIP: python3 absent — reasoning-shape probe tests"
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
