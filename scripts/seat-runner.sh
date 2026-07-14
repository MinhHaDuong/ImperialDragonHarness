#!/usr/bin/env bash
# seat-runner — run an agnostic CLI reviewer (aider --ask) inside an OS-level
# rootless container (podman) over a LOCAL branch diff. No forge round-trip.
#
# Ticket 0217 (sandbox-runner reviewer-seat spinoff), embodying the "review is
# CI" model: the seat is a contained job over a read-only checkout, emitting
# findings on stdout; the orchestrator owns everything else.
#
# Why podman, not bwrap: this host sets
# kernel.apparmor_restrict_unprivileged_userns=1 and ships AppArmor userns
# profiles for podman/crun/runc but not bwrap — rootless podman is the
# sandbox that works unprivileged here, and a container IS the CI-runner
# primitive the architecture wants.
#
# Containment:
#   - repo + diff mounted READ-ONLY; container rootfs --read-only
#     (kernel-enforced; a write attempt fails even for a misbehaving seat)
#   - HOME is a throwaway tmpfs; the real $HOME is NOT mounted. The reviewer CLI
#     is exposed by allowlisting ONLY its uv-tool venv and its interpreter (both
#     pure code) — never all of ~/.local, which also holds keyrings, wallets,
#     jupyter/neo4j tokens, and browser cookies. The self-test proves ~/.local
#     is scoped, not wholesale-mounted.
#   - env is explicitly constructed (no BASH_ENV, no inherited secrets). A
#     per-seat endpoint credential MAY be injected via --credential-env, read
#     from the runner's own env and passed as a bare `-e OPENAI_API_KEY` so it
#     never enters podman argv; a local unauthenticated endpoint uses an inline
#     dummy OPENAI_API_KEY instead.
#   - CREDENTIAL SCRUB (0207): when a real credential is injected, its exact
#     runtime value is redacted from the reviewer's captured stdout/stderr
#     before any of them is echoed (findings, failure tail, WARN cat). This is
#     a literal value substitution — defense-in-depth against the seat's client
#     verbatim-echoing the key (e.g. an auth-error line), NOT a semantic filter.
#   - NETWORK IS DENY-BY-DEFAULT: the seat runs under --network=none, so its
#     netns has no interface but loopback — no route to any host. It reaches
#     the ONE model endpoint through a bind-mounted Unix-domain socket
#     (/relay.sock), a filesystem object rather than a network route. Host-side,
#     scripts/seat-runner/net-relay.py listens on that socket and forwards to
#     the real endpoint; container-side the same relay presents the socket as a
#     loopback TCP port (loopback is per-netns, alive under --network=none) so
#     aider/litellm get the OPENAI_API_BASE they expect. A misbehaving or
#     prompt-injected seat can reach the relayed endpoint and NO OTHER NETWORK
#     DESTINATION — no arbitrary outbound host, no domain-fronting exfil.
#     (Replaces the v1 --network=host gap: pasta/slirp4netns do full outbound
#     NAT with no per-destination allowlist, so they were rejected.) The relay
#     forwards raw bytes to a PLAIN host:port; it neither terminates nor inspects
#     TLS. A plain-HTTP endpoint (0217's local target) uses the same port on
#     both sides. An HTTPS cloud endpoint (0207) rides through the same raw pump
#     end-to-end: --add-host maps the real hostname to loopback and the seat's
#     client dials an in-container bridge on 8443 (a --userns=keep-id seat cannot
#     bind 443), so the client still presents valid SNI and validates the real
#     cert — the relay just moves the encrypted bytes; it never sees plaintext.
#   - PER-SEAT TIMEOUT: every container invocation is wrapped in `timeout`
#     (SEAT_TIMEOUT, default 600s). timeout SIGKILLs only the podman CLIENT —
#     rootless conmon keeps the container alive — so each seat is named and
#     force-removed after the run and in the EXIT trap; a hung or adversarial
#     seat is both reported non-zero AND reaped, never left orphaned.
#   - the containment self-test FAILS LOUD if the sandbox itself does not
#     start: a blocked write only counts when the probe also proves the
#     sandbox executes. Run it standalone with --self-test-only (no endpoint,
#     no diff) to prove containment with podman + the image alone.
#
# Usage:
#   seat-runner.sh --branch BRANCH [--repo PATH] [--base REF]
#                  [--endpoint URL] [--model NAME] [--out FILE]
#                  [--credential-env VAR] [--health-path PATH]
#   seat-runner.sh --self-test-only      # prove containment; no endpoint, no diff
#
#   --credential-env VAR : read the endpoint's API key from env var VAR and pass
#                          it to the seat via env (never argv). Default: a dummy
#                          key for a local, unauthenticated endpoint.
#   --health-path PATH   : probe path appended to the endpoint ORIGIN (default
#                          /health); empty string skips the reachability probe.
#
# Env: SEAT_TIMEOUT (per-seat wall-clock cap, seconds; default 600)
set -euo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
RELAY="${SELF_DIR}/seat-runner/net-relay.py"

REPO="$(pwd)"
BASE="origin/main"
BRANCH=""
ENDPOINT="http://127.0.0.1:8012/v1"
MODEL="openai/devstral-small-2"
OUT="/dev/stdout"
IMAGE="localhost/seat-runner:v1"   # ubuntu:24.04 + python3 + git + ca-certs
SEAT_TIMEOUT="${SEAT_TIMEOUT:-600}"
SELF_TEST_ONLY=0
CREDENTIAL_ENV=""          # env var holding the endpoint's API key (never argv)
HEALTH_PATH="/health"      # probe path appended to the origin; "" skips the probe

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)           REPO="$2"; shift 2 ;;
        --base)           BASE="$2"; shift 2 ;;
        --branch)         BRANCH="$2"; shift 2 ;;
        --endpoint)       ENDPOINT="$2"; shift 2 ;;
        --model)          MODEL="$2"; shift 2 ;;
        --out)            OUT="$2"; shift 2 ;;
        --credential-env) CREDENTIAL_ENV="$2"; shift 2 ;;
        --health-path)    HEALTH_PATH="$2"; shift 2 ;;
        --self-test-only) SELF_TEST_ONLY=1; shift ;;
        *) echo "seat-runner: unknown arg $1" >&2; exit 2 ;;
    esac
done

command -v podman >/dev/null || { echo "seat-runner: podman not installed" >&2; exit 1; }

# ── Endpoint decomposition (unconditional; the health probe AND the relay both
#    need it). Origin = SCHEME://EP where EP is the authority host[:port]; the
#    container reaches the endpoint through its own loopback, bridged over the
#    relay socket. ──────────────────────────────────────────────────────────────
SCHEME="${ENDPOINT%%://*}"
EP="${ENDPOINT#*://}"; EP="${EP%%/*}"                                     # host[:port]
ENDPOINT_PATH="${ENDPOINT#*://}"; ENDPOINT_PATH="${ENDPOINT_PATH#"$EP"}"  # /path… or ""
ENDPOINT_HOST="${EP%%:*}"
ENDPOINT_PORT="${EP##*:}"
if [[ "$ENDPOINT_PORT" == "$ENDPOINT_HOST" ]]; then   # no explicit port
    case "$SCHEME" in https) ENDPOINT_PORT=443 ;; *) ENDPOINT_PORT=80 ;; esac
fi

# The in-container OPENAI_API_BASE (CONTAINER_BASE) and the bridge port
# (CONTAINER_PORT). http: same port, host swapped to loopback — byte-identical
# to v1. https: a --userns=keep-id seat cannot bind a <1024 port (EACCES), so
# the bridge listens on 8443 and --add-host maps the real hostname to 127.0.0.1;
# the client still presents valid SNI/cert for the real host and TLS stays
# end-to-end to the cloud through the raw (byte-pumping) relay.
ADD_HOST_ARGS=()
if [[ "$SCHEME" == https ]]; then
    CONTAINER_PORT=8443
    CONTAINER_BASE="${SCHEME}://${ENDPOINT_HOST}:${CONTAINER_PORT}${ENDPOINT_PATH}"
    ADD_HOST_ARGS=(--add-host "${ENDPOINT_HOST}:127.0.0.1")
else
    CONTAINER_PORT="$ENDPOINT_PORT"
    CONTAINER_BASE="${ENDPOINT/${ENDPOINT_HOST}/127.0.0.1}"
fi

# ── Per-seat credential injection. Default: a dummy key for a local endpoint
#    (NOT a secret), passed inline. With --credential-env NAME: read the secret
#    from that env var HERE, export it, and pass the BARE `-e OPENAI_API_KEY`
#    form so podman reads the value from the runner's env — never argv (argv
#    leaks to `ps -ef`). Fail loud if the named var is empty; never echo it. ────
CRED_ARGS=(-e OPENAI_API_KEY=local-dummy)
if [[ -n "$CREDENTIAL_ENV" ]]; then
    if [[ -z "${!CREDENTIAL_ENV:-}" ]]; then
        echo "seat-runner: FATAL --credential-env ${CREDENTIAL_ENV} names an empty or unset variable" >&2
        exit 1
    fi
    export OPENAI_API_KEY="${!CREDENTIAL_ENV}"
    CRED_ARGS=(-e OPENAI_API_KEY)
fi

if [[ "$SELF_TEST_ONLY" -eq 0 ]]; then
    [[ -n "$BRANCH" ]] || { echo "seat-runner: --branch required" >&2; exit 2; }
    # Fail loud if the endpoint is down (0217: unreachable endpoint = non-zero).
    # Build the probe URL from the ORIGIN + --health-path, NOT ${ENDPOINT%/v1}
    # (which double-prefixes /api for an /api/v1 endpoint). Empty --health-path
    # skips the probe for endpoints that expose no health route.
    if [[ -n "$HEALTH_PATH" ]]; then
        curl -sf --max-time 5 "${SCHEME}://${EP}${HEALTH_PATH}" >/dev/null \
            || { echo "seat-runner: endpoint ${ENDPOINT} unreachable" >&2; exit 1; }
    fi
fi

HOMEDIR="$HOME"   # --userns=keep-id keeps uids aligned; paths match host

# A code-mount root derived by walking up from a resolved binary must never be
# $HOME, ~/.local, or an ancestor of $HOME: mounting any of those drags the real
# home (keyrings, wallets, tokens) into the seat, defeating the whole scoping.
# Fail loud, naming the offending path, rather than silently over-exposing.
_reject_home_exposing_mount() {  # role resolved-path
    local _role="$1" _path="$2"
    if [[ "$_path" == "$HOMEDIR" || "$_path" == "$HOMEDIR"/.local \
          || "$HOMEDIR" == "$_path" || "$HOMEDIR" == "$_path"/* ]]; then
        echo "seat-runner: FATAL refusing to mount ${_role} '${_path}' — it is \$HOME, ~/.local, or an ancestor of \$HOME (would expose secrets)" >&2
        exit 1
    fi
}

# Resolve the reviewer CLI and its interpreter, and mount ONLY those two pure-
# code trees — never all of ~/.local (keyrings, wallets, tokens live there).
# aider's ~/.local/bin launcher is a symlink into a uv-tool venv whose python is
# itself a symlink to a uv-managed interpreter; both must be reachable.
AIDER_REAL=""
SEAT_CODE_MOUNTS=()
if _aider="$(command -v aider 2>/dev/null)"; then
    AIDER_REAL="$(readlink -f "$_aider")"
    _venv="$(dirname "$(dirname "$AIDER_REAL")")"
    # The resolved root must actually be a venv, and must not expose $HOME.
    [[ -f "$_venv/pyvenv.cfg" ]] \
        || { echo "seat-runner: FATAL resolved venv root '${_venv}' has no pyvenv.cfg — refusing to mount a non-venv tree" >&2; exit 1; }
    _reject_home_exposing_mount "venv" "$_venv"
    SEAT_CODE_MOUNTS+=(-v "${_venv}:${_venv}:ro")
    if _py="$(readlink -f "${_venv}/bin/python" 2>/dev/null)" && [[ -n "$_py" ]]; then
        _pyhome="$(dirname "$(dirname "$_py")")"
        _reject_home_exposing_mount "interpreter" "$_pyhome"
        SEAT_CODE_MOUNTS+=(-v "${_pyhome}:${_pyhome}:ro")
    fi
fi
if [[ "$SELF_TEST_ONLY" -eq 0 && -z "$AIDER_REAL" ]]; then
    echo "seat-runner: FATAL aider not found on PATH" >&2; exit 1
fi

WORK=$(mktemp -d)
RELAY_PID=""
SEAT_CONTAINERS=()
cleanup() {
    [[ -n "$RELAY_PID" ]] && kill "$RELAY_PID" 2>/dev/null || true
    for _c in ${SEAT_CONTAINERS[@]+"${SEAT_CONTAINERS[@]}"}; do
        podman rm -f "$_c" >/dev/null 2>&1 || true
    done
    rm -rf "$WORK"
}
trap cleanup EXIT

# ── Host-side relay: /relay.sock ⇄ the real endpoint. The container binds the
#    socket file; under --network=none it has no other route out. ──────────────
python3 "$RELAY" --listen "unix:${WORK}/relay.sock" \
                 --connect "tcp:${ENDPOINT_HOST}:${ENDPOINT_PORT}" &
RELAY_PID=$!
for _ in $(seq 1 50); do [[ -S "${WORK}/relay.sock" ]] && break; sleep 0.1; done
[[ -S "${WORK}/relay.sock" ]] || { echo "seat-runner: FATAL relay socket never appeared" >&2; exit 1; }

# ── Read-only checkout + review prompt (skipped for --self-test-only) ─────────
cat > "$WORK/prompt.txt" <<'PROMPT'
You are an advisory code reviewer on a merge gate panel. Review the unified
diff in /review.diff (the full checkout is at /repo, read-only, for context).
Report only findings you can ground in the diff. For EACH finding emit exactly
one line in this shape:
FINDING|severity=verifiable-or-consider|file=PATH:LINE|rationale=ONE SENTENCE
verifiable = objectively checkable defect (logic, broken reference, format
violation); consider = judgment-call improvement. After the findings emit one
line: SUMMARY|findings=N|verdict=approve-or-revise
If there are no findings, emit only the SUMMARY line with findings=0.
PROMPT

if [[ "$SELF_TEST_ONLY" -eq 1 ]]; then
    # No diff needed; give run_seat valid (empty) mount targets.
    mkdir -p "$WORK/clone"; : > "$WORK/review.diff"
else
    git clone --quiet --local --no-hardlinks "$REPO" "$WORK/clone"
    git -C "$WORK/clone" checkout --quiet "$BRANCH"
    git -C "$WORK/clone" diff "${BASE}...${BRANCH}" > "$WORK/review.diff"
    [[ -s "$WORK/review.diff" ]] || { echo "seat-runner: empty diff ${BASE}...${BRANCH}" >&2; exit 1; }
fi

# ── The sandboxed seat launcher (timeout-wrapped, reaped; network-denied) ─────
run_seat() {
    local cname="seatrun-$$-${RANDOM}"
    local rc=0
    SEAT_CONTAINERS+=("$cname")
    timeout -k 5 "$SEAT_TIMEOUT" podman run --rm \
        --name "$cname" \
        --network=none \
        --userns=keep-id \
        --read-only \
        --tmpfs "$HOMEDIR":rw,size=256m \
        --tmpfs /tmp:rw,size=64m \
        ${SEAT_CODE_MOUNTS[@]+"${SEAT_CODE_MOUNTS[@]}"} \
        ${ADD_HOST_ARGS[@]+"${ADD_HOST_ARGS[@]}"} \
        -v "$WORK/clone":/repo:ro \
        -v "$WORK/review.diff":/review.diff:ro \
        -v "$WORK/prompt.txt":/prompt.txt:ro \
        -v "$WORK/relay.sock":/relay.sock:rw \
        -v "$RELAY":/net-relay.py:ro \
        -e HOME="$HOMEDIR" \
        -e PATH="/usr/bin:/bin" \
        -e TERM=dumb \
        -e COLUMNS=500 \
        ${CRED_ARGS[@]+"${CRED_ARGS[@]}"} \
        -e OPENAI_API_BASE="$CONTAINER_BASE" \
        -w /repo \
        "$IMAGE" "$@" || rc=$?
    # timeout kills only the podman client; force-reap the container it orphaned.
    podman rm -f "$cname" >/dev/null 2>&1 || true
    return "$rc"
}

# ── Containment self-test (0217: proven, not assumed; alive-then-blocked) ─────
echo "seat-runner: containment self-test..." >&2
PROBE=$(run_seat bash -c '
    echo SANDBOX-ALIVE
    touch /repo/PWNED 2>/dev/null && echo WRITE-ALLOWED || echo WRITE-BLOCKED
    cat '"$HOMEDIR"'/.ssh/id_* '"$HOMEDIR"'/.claude/scripts/bash-env.sh \
        '"$HOMEDIR"'/.local/share/keyrings/* '"$HOMEDIR"'/.local/share/kwalletd/* 2>/dev/null \
        | grep -q . && echo SECRET-READ || echo SECRET-BLOCKED
    if ls '"$HOMEDIR"'/.local/share 2>/dev/null | grep -qvx uv; then echo LOCAL-OVERMOUNTED; else echo LOCAL-SCOPED; fi
    if timeout 3 bash -c ": < /dev/tcp/1.1.1.1/443" 2>/dev/null; then echo NET-ALLOWED; else echo NET-BLOCKED; fi
') || { echo "seat-runner: FATAL sandbox failed to start" >&2; exit 1; }
grep -q SANDBOX-ALIVE  <<<"$PROBE" || { echo "seat-runner: FATAL probe did not run" >&2; exit 1; }
grep -q WRITE-BLOCKED  <<<"$PROBE" || { echo "seat-runner: FATAL repo write was NOT blocked" >&2; exit 1; }
grep -q SECRET-BLOCKED <<<"$PROBE" || { echo "seat-runner: FATAL secret read was NOT blocked" >&2; exit 1; }
grep -q LOCAL-SCOPED   <<<"$PROBE" || { echo "seat-runner: FATAL ~/.local over-mounted (secret-exposure regression?)" >&2; exit 1; }
grep -q NET-BLOCKED    <<<"$PROBE" || { echo "seat-runner: FATAL external network was reachable (network-deny regression?)" >&2; exit 1; }
echo "seat-runner: containment OK (sandbox alive; repo write blocked; secrets unreachable; ~/.local scoped to CLI venv; external network denied)" >&2

if [[ "$SELF_TEST_ONLY" -eq 1 ]]; then
    echo "seat-runner: --self-test-only complete." >&2
    exit 0
fi

# ── Run the reviewer seat ────────────────────────────────────────────────────
# Container-side bridge: present the bind-mounted socket as the loopback TCP
# port aider expects (net-relay.py, reversed), wait for it to bind, then exec
# the reviewer. Loopback is per-netns and stays up under --network=none. Run
# under bash, not the image's dash /bin/sh — the readiness wait uses /dev/tcp,
# a bash builtin dash lacks (without it the wait degrades to a blind sleep).
echo "seat-runner: reviewing ${BRANCH} vs ${BASE} with ${MODEL}..." >&2
BRIDGE_AND_REVIEW=$(cat <<EOF
python3 /net-relay.py --listen tcp:127.0.0.1:${CONTAINER_PORT} --connect unix:/relay.sock &
for _ in \$(seq 1 50); do (: < /dev/tcp/127.0.0.1/${CONTAINER_PORT}) 2>/dev/null && break; sleep 0.1; done
exec ${AIDER_REAL} \\
    --no-git --chat-mode ask --model "${MODEL}" \\
    --message "\$(cat /prompt.txt)" \\
    --read /review.diff \\
    --yes-always --no-check-update --no-show-model-warnings --no-pretty \\
    --no-stream --map-tokens 0
EOF
)
review_rc=0
run_seat bash -c "$BRIDGE_AND_REVIEW" \
    > "$WORK/raw.out" 2> "$WORK/raw.err" \
    || review_rc=$?

# ── Credential scrub (0207 red-team, mitigation a) ────────────────────────────
# The reviewer reads attacker-controllable diff text and its output flows back
# out, so a prompt-injected diff could coax the injected key into that output.
# When a REAL credential was injected (--credential-env), redact its exact value
# from BOTH capture files IN PLACE, BEFORE any path that echoes them: the
# failure-tail below, the contract-grep that writes $OUT, and the WARN cat. The
# secret is read from the process env (OPENAI_API_KEY, exported above), never
# passed on argv; file paths are the only argv. Provider-agnostic — it
# substitutes the runtime value, not a vendor key pattern. No-op for the local
# dummy key (CREDENTIAL_ENV empty).
if [[ -n "$CREDENTIAL_ENV" ]]; then
    python3 - "$WORK/raw.out" "$WORK/raw.err" <<'PY'
import os, sys

secret = os.environ.get("OPENAI_API_KEY", "")
if secret:
    for path in sys.argv[1:]:
        try:
            with open(path, "r", errors="surrogateescape") as fh:
                data = fh.read()
        except FileNotFoundError:
            continue
        redacted = data.replace(secret, "[REDACTED-CREDENTIAL]")
        if redacted != data:
            with open(path, "w", errors="surrogateescape") as fh:
                fh.write(redacted)
PY
fi

if [[ "$review_rc" -ne 0 ]]; then
    echo "seat-runner: reviewer exited non-zero (or timed out); stderr follows" >&2
    tail -20 "$WORK/raw.err" >&2
    exit 1
fi

# ── Pre-filter: structural contract lines only (harvest is the normalizer) ────
grep -E '^(FINDING|SUMMARY)\|' "$WORK/raw.out" > "$OUT" || {
    echo "seat-runner: WARN no contract-shaped lines in reviewer output; raw output follows" >&2
    cat "$WORK/raw.out" >&2
    exit 1
}
echo "seat-runner: done." >&2
