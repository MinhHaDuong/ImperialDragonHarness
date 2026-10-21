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

# Concurrency for a batch of independent jobs: min(jobs, nproc / 2), at least 1.
# Half the threads, because a job (pytest in particular) is itself multi-process.
# LOCAL_CI_CONCURRENCY caps it lower or higher by hand.
concurrency() {
    local jobs=$1 cap
    cap=${LOCAL_CI_CONCURRENCY:-$(( $(nproc) / 2 ))}
    [ "$cap" -ge 1 ] || cap=1
    [ "$jobs" -lt "$cap" ] && echo "$jobs" || echo "$cap"
}

# A copy of the workflow whose `name:` carries this runner's tag. act names the
# job container act-<workflow>-<job>-<hash> and the hash is the same for every
# runner, so two runners on the same job collided on the container name in the
# one rootless podman storage (reproduced 2026-10-21; the clone path and the
# separate podman services do not matter). Usage: tagged_workflow SRC DEST TAG
tagged_workflow() {
    sed "0,/^name: .*/s//name: CI-$3/" "$1" > "$2"
    grep -q "^name: CI-$3\$" "$2" || { echo "local-ci: workflow has no top-level name: line to tag" >&2; return 1; }
}

# Run "$fn item" for every item, at most $limit at a time, then return the
# number of failed calls via $pool_failed. Each call must report through files.
pool_failed=0
run_pool() {
    local limit=$1 fn=$2 item running=0
    shift 2
    pool_failed=0
    for item in "$@"; do
        if [ "$running" -ge "$limit" ]; then
            wait -n || pool_failed=$((pool_failed + 1))
            running=$((running - 1))
        fi
        "$fn" "$item" &
        running=$((running + 1))
    done
    while [ "$running" -gt 0 ]; do
        wait -n || pool_failed=$((pool_failed + 1))
        running=$((running - 1))
    done
}
