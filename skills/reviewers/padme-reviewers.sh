#!/usr/bin/env bash
# On-demand, local-only reviewer panel over Padmé's existing llama-server.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEWERS_PANEL="$SELF_DIR/panel-padme.yml"
export REVIEWERS_PANEL

if [[ "${PADME_SEAT_RUNNER:-}" == 1 ]]; then
    exec "$SELF_DIR/../../scripts/seat-runner.sh" "$@" \
        --client direct --reasoning-effort none --health-path /v1/models
fi

if [[ "${1:-}" != request ]]; then
    exec "$SELF_DIR/reviewers.sh" "$@"
fi

# Keep the forward alive for one request. A failed SSH startup must not make
# reviewers silently fall back to paid seats, and trap cleanup reaps the tunnel.
ssh -F "$HOME/.ssh/config" -o BatchMode=yes -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=15 -N -L 127.0.0.1:18080:127.0.0.1:8080 padme &
tunnel_pid=$!
cleanup() { kill "$tunnel_pid" 2>/dev/null || true; wait "$tunnel_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 30); do
    if ! kill -0 "$tunnel_pid" 2>/dev/null; then break; fi
    if curl -fsS --max-time 2 http://127.0.0.1:18080/v1/models >/dev/null 2>&1; then
        ready=1; break
    fi
    sleep 0.2
done
[[ "$ready" -eq 1 ]] || { echo "padme-reviewers: tunnel unavailable" >&2; exit 1; }

PADME_SEAT_RUNNER=1 SEAT_RUNNER="$SELF_DIR/padme-reviewers.sh" \
    "$SELF_DIR/reviewers.sh" "$@"
