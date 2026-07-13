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
#   - env is explicitly constructed (no BASH_ENV, no inherited secrets; only
#     a dummy OPENAI_API_KEY for the local endpoint)
#   - NETWORK IS DENY-BY-DEFAULT: the seat runs under --network=none, so its
#     netns has no interface but loopback — no route to any host. It reaches
#     the ONE model endpoint through a bind-mounted Unix-domain socket
#     (/relay.sock), a filesystem object rather than a network route. Host-side,
#     scripts/seat-runner/net-relay.py listens on that socket and forwards to
#     the real endpoint; container-side the same relay presents the socket as a
#     loopback TCP port (loopback is per-netns, alive under --network=none) so
#     aider/litellm get the OPENAI_API_BASE they expect. A misbehaving or
#     prompt-injected seat can reach the relayed endpoint and NOTHING else — no
#     arbitrary outbound host, no domain-fronting exfil. (Replaces the v1
#     --network=host gap: pasta/slirp4netns do full outbound NAT with no
#     per-destination allowlist, so they were rejected.)
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
#   seat-runner.sh --self-test-only      # prove containment; no endpoint, no diff
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

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)           REPO="$2"; shift 2 ;;
        --base)           BASE="$2"; shift 2 ;;
        --branch)         BRANCH="$2"; shift 2 ;;
        --endpoint)       ENDPOINT="$2"; shift 2 ;;
        --model)          MODEL="$2"; shift 2 ;;
        --out)            OUT="$2"; shift 2 ;;
        --self-test-only) SELF_TEST_ONLY=1; shift ;;
        *) echo "seat-runner: unknown arg $1" >&2; exit 2 ;;
    esac
done

command -v podman >/dev/null || { echo "seat-runner: podman not installed" >&2; exit 1; }

if [[ "$SELF_TEST_ONLY" -eq 0 ]]; then
    [[ -n "$BRANCH" ]] || { echo "seat-runner: --branch required" >&2; exit 2; }
    # Fail loud if the endpoint is down (0217: unreachable endpoint = non-zero).
    curl -sf --max-time 5 "${ENDPOINT%/v1}/health" >/dev/null \
        || { echo "seat-runner: endpoint ${ENDPOINT} unreachable" >&2; exit 1; }
fi

# Endpoint host:port for the host-side relay. The container reaches the SAME
# port on its own loopback (bridged through the socket), so only the host part
# changes to 127.0.0.1 for the in-container OPENAI_API_BASE.
EP="${ENDPOINT#*://}"; EP="${EP%%/*}"
ENDPOINT_HOST="${EP%%:*}"
ENDPOINT_PORT="${EP##*:}"
if [[ "$ENDPOINT_PORT" == "$ENDPOINT_HOST" ]]; then   # no explicit port
    case "$ENDPOINT" in https://*) ENDPOINT_PORT=443 ;; *) ENDPOINT_PORT=80 ;; esac
fi
CONTAINER_BASE="${ENDPOINT/${ENDPOINT_HOST}/127.0.0.1}"

HOMEDIR="$HOME"   # --userns=keep-id keeps uids aligned; paths match host

# Resolve the reviewer CLI and its interpreter, and mount ONLY those two pure-
# code trees — never all of ~/.local (keyrings, wallets, tokens live there).
# aider's ~/.local/bin launcher is a symlink into a uv-tool venv whose python is
# itself a symlink to a uv-managed interpreter; both must be reachable.
AIDER_REAL=""
SEAT_CODE_MOUNTS=()
if _aider="$(command -v aider 2>/dev/null)"; then
    AIDER_REAL="$(readlink -f "$_aider")"
    _venv="$(dirname "$(dirname "$AIDER_REAL")")"
    SEAT_CODE_MOUNTS+=(-v "${_venv}:${_venv}:ro")
    if _py="$(readlink -f "${_venv}/bin/python" 2>/dev/null)" && [[ -n "$_py" ]]; then
        _pyhome="$(dirname "$(dirname "$_py")")"
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
        -v "$WORK/clone":/repo:ro \
        -v "$WORK/review.diff":/review.diff:ro \
        -v "$WORK/prompt.txt":/prompt.txt:ro \
        -v "$WORK/relay.sock":/relay.sock:rw \
        -v "$RELAY":/net-relay.py:ro \
        -e HOME="$HOMEDIR" \
        -e PATH="/usr/bin:/bin" \
        -e TERM=dumb \
        -e COLUMNS=500 \
        -e OPENAI_API_KEY=local-dummy \
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
# port aider expects (net-relay.py, reversed), then exec the reviewer. Loopback
# is per-netns and stays up under --network=none.
echo "seat-runner: reviewing ${BRANCH} vs ${BASE} with ${MODEL}..." >&2
BRIDGE_AND_REVIEW=$(cat <<EOF
python3 /net-relay.py --listen tcp:127.0.0.1:${ENDPOINT_PORT} --connect unix:/relay.sock &
for _ in \$(seq 1 50); do (: < /dev/tcp/127.0.0.1/${ENDPOINT_PORT}) 2>/dev/null && break; sleep 0.1; done
exec ${AIDER_REAL} \\
    --no-git --chat-mode ask --model "${MODEL}" \\
    --message "\$(cat /prompt.txt)" \\
    --read /review.diff \\
    --yes-always --no-check-update --no-show-model-warnings --no-pretty \\
    --no-stream --map-tokens 0
EOF
)
run_seat sh -c "$BRIDGE_AND_REVIEW" \
    > "$WORK/raw.out" 2> "$WORK/raw.err" \
    || { echo "seat-runner: reviewer exited non-zero (or timed out); stderr follows" >&2; tail -20 "$WORK/raw.err" >&2; exit 1; }

# ── Pre-filter: structural contract lines only (harvest is the normalizer) ────
grep -E '^(FINDING|SUMMARY)\|' "$WORK/raw.out" > "$OUT" || {
    echo "seat-runner: WARN no contract-shaped lines in reviewer output; raw output follows" >&2
    cat "$WORK/raw.out" >&2
    exit 1
}
echo "seat-runner: done." >&2
