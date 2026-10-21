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
    local limit=$1 fn=$2 item running=0 i=0 dir f pids=()
    shift 2
    dir=$(mktemp -d "${work:-${TMPDIR:-/tmp}}/pool.XXXXXX") || return 1
    for item in "$@"; do
        if [ "$running" -ge "$limit" ]; then
            # Throttle only. wait -n's status is not trusted: it can report 127 when
            # two jobs end together, and counting that as a failure over-reported.
            wait -n 2>/dev/null || true
            running=$((running - 1))
        fi
        # Plain command, so the caller's set -e stays live inside $fn; the EXIT trap
        # records the status either way. A job killed outright leaves no file.
        ( trap 'echo $? > "$dir/$i"' EXIT; "$fn" "$item" ) &
        pids+=("$!")
        running=$((running + 1))
        i=$((i + 1))
    done
    # Exact completion: wait on this pool's own pids, never on the caller's other
    # background jobs (the podman service must keep running).
    for item in ${pids[@]+"${pids[@]}"}; do wait "$item" 2>/dev/null || true; done
    # Exact failure count: one status file per item, written by the job itself.
    pool_failed=0
    # Counted over every index: a missing file (job killed) is a failure.
    for ((f = 0; f < i; f++)); do
        [ "$(cat "$dir/$f" 2>/dev/null)" = 0 ] || pool_failed=$((pool_failed + 1))
    done
    rm -rf "$dir"
}

# Print the arguments one per line, first occurrence only, order kept. A job named
# twice would otherwise run twice in parallel on one container name.
dedupe_args() {
    [ "$#" -eq 0 ] || printf '%s\n' "$@" | awk '!seen[$0]++'
}

# Run a command as the leader of its own process group, so a signal can reach
# act and its children and not only the shell around them. The group id is
# recorded in $work/<name>.pgid for kill_groups. Usage: group_run NAME CMD...
group_run() {
    local name=$1 pid
    shift
    setsid "$@" &
    pid=$!
    echo "$pid" > "$work/$name.pgid"
    wait "$pid"
}

# Kill every recorded group. Called by the INT/TERM trap before the EXIT trap
# removes $work and stops the podman service, so no act is orphaned.
kill_groups() {
    local f
    for f in "$work"/*.pgid; do
        [ -e "$f" ] || continue
        kill -- "-$(cat "$f")" 2>/dev/null || true
    done
}
