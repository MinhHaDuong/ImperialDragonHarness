# Sourced by scripts/local-ci.sh and scripts/local-ci-negative-controls.sh.
# Expects: $here (this directory), $work (a scratch directory the caller owns).
# Sets:    $sock, $service_pid, $image. The caller's EXIT trap calls stop_service.

image=localhost/act-runner:dev
sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/local-ci-$$.sock"  # unix socket paths are capped near 108 bytes
service_pid=

stop_service() {
    if [ -n "$service_pid" ]; then
        kill "$service_pid" 2>/dev/null || true
        wait "$service_pid" 2>/dev/null || true
    fi
    rm -f "$sock"
}

# A dedicated podman service, so the keep-id setting does not leak into the
# user's default podman.
start_service() {
    CONTAINERS_CONF="$here/containers.conf" podman system service --time=0 "unix://$sock" 2> "$work/service.log" &
    service_pid=$!
    for _ in $(seq 1 50); do [ -S "$sock" ] && break; sleep 0.1; done
    [ -S "$sock" ] || { echo "local-ci: podman service did not start: $(cat "$work/service.log")" >&2; exit 2; }
}

# Rebuild when the Containerfile changed since the image was built.
ensure_image() {
    local want have
    want=$(sha256sum "$here/Containerfile" | cut -c1-16)
    have=$(podman image inspect --format '{{index .Labels "ci-local.sha"}}' "$image" 2>/dev/null || true)
    if [ "$have" != "$want" ]; then
        echo "local-ci: building $image"
        podman build -q --label "ci-local.sha=$want" -t "$image" "$here" >/dev/null
    fi
}
