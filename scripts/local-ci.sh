#!/usr/bin/env bash
# Run the repository's CI workflow locally, job by job, with `act` in podman.
#
# The workflow file stays the single definition of the checks; this script only
# supplies what a forge runner would: a clean clone, a runner image, a
# pull_request event and a token. Usage:
#
#   scripts/local-ci.sh [job ...]     # default: every job of the workflow
#
# What is tested: the COMMITTED HEAD of the current checkout, cloned fresh. An
# uncommitted change is not tested (a warning says so). The forge tests the
# merge of the PR into its base; this tests the branch head alone.
#
# Requires act, podman, gh (authenticated) and network access to the origin.
# The jobs receive the user's `gh` token: acceptable while the only code that
# runs is the author's own. Exit status is non-zero if any job fails, or if the
# job list is not the workflow's. `act -j` honours only the last -j it is given,
# hence one invocation per job.
set -euo pipefail

workflow=.github/workflows/CI.yml
root=$(git rev-parse --show-toplevel)
here="$root/ci-local"
image=localhost/act-runner:dev
work=$(mktemp -d)
sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/local-ci-$$.sock"  # unix socket paths are capped near 108 bytes
service_pid=
trap 'if [ -n "$service_pid" ]; then kill "$service_pid" 2>/dev/null || true; wait "$service_pid" 2>/dev/null || true; fi; rm -rf "$work" "$sock"' EXIT
trap 'exit 130' INT TERM

for tool in act podman gh; do
    command -v "$tool" >/dev/null || { echo "local-ci: $tool not found" >&2; exit 2; }
done
# An inherited .actrc can add options such as --dryrun that make every job "pass".
for rc in "$HOME/.actrc" "$root/.actrc"; do
    [ ! -e "$rc" ] || { echo "local-ci: refusing to run with $rc present (it can change act's behaviour)" >&2; exit 2; }
done

head=$(git rev-parse --short HEAD)
echo "local-ci: testing committed HEAD $head of $(git rev-parse --abbrev-ref HEAD)"
if [ -n "$(git status --porcelain)" ]; then
    echo "local-ci: WARNING: uncommitted changes are NOT tested" >&2
fi

# A dedicated podman service, so the keep-id setting does not leak into the
# user's default podman.
CONTAINERS_CONF="$here/containers.conf" podman system service --time=0 "unix://$sock" 2> "$work/service.log" &
service_pid=$!
for _ in $(seq 1 50); do [ -S "$sock" ] && break; sleep 0.1; done
[ -S "$sock" ] || { echo "local-ci: podman service did not start: $(cat "$work/service.log")" >&2; exit 2; }

# Rebuild when the Containerfile changed since the image was built.
want=$(sha256sum "$here/Containerfile" | cut -c1-16)
have=$(podman image inspect --format '{{index .Labels "ci-local.sha"}}' "$image" 2>/dev/null || true)
if [ "$have" != "$want" ]; then
    echo "local-ci: building $image"
    podman build -q --label "ci-local.sha=$want" -t "$image" "$here" >/dev/null
fi

# act's default copy drops .git, so run from a real clone bind-mounted into the
# container. Origin points at the forge so `gh` resolves {owner}/{repo}.
origin=$(git remote get-url origin)
clone="$work/clone"
git clone --quiet --no-hardlinks "$root" "$clone"
git -C "$clone" remote set-url origin "$origin"
git -C "$clone" fetch --quiet origin

pr=$(gh pr view --json number --jq .number 2>/dev/null || true)
base=$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null || true)
if [ -z "$pr" ] || [ -z "$base" ]; then
    echo "local-ci: no open PR for this branch; assuming base main, so every open PR counts as a sibling" >&2
    pr=0
    base=main
fi
printf '{"pull_request":{"number":%s,"base":{"ref":"%s"}},"number":%s}\n' "$pr" "$base" "$pr" > "$work/event.json"
token=$(gh auth token)
printf 'GITHUB_TOKEN=%s\n' "$token" > "$work/secrets"
chmod 600 "$work/secrets"

act_in_clone() { (cd "$clone" && DOCKER_HOST="unix://$sock" act pull_request "$@"); }

# The job list must be the workflow's, not whatever discovery printed.
expected=$(python3 -c 'import sys, yaml; print(len(yaml.safe_load(open(sys.argv[1]))["jobs"]))' "$clone/$workflow")
listing=$(act_in_clone -l 2> "$work/list.log") || { echo "local-ci: act -l failed: $(cat "$work/list.log")" >&2; exit 2; }
mapfile -t listed < <(awk 'NR>1 && NF {print $2}' <<< "$listing")
if [ "$#" -gt 0 ]; then
    jobs=("$@")
else
    jobs=("${listed[@]}")
    if [ "${#jobs[@]}" -eq 0 ] || [ "${#jobs[@]}" -ne "$expected" ]; then
        echo "local-ci: found ${#jobs[@]} jobs, the workflow defines $expected; refusing to report a pass" >&2
        exit 2
    fi
fi

fail=0
for job in "${jobs[@]}"; do
    echo "== $job"
    git -C "$clone" reset -q --hard HEAD
    git -C "$clone" clean -qfdx
    if timeout 1800 bash -c 'cd "$1" && shift && DOCKER_HOST="unix://$1" act pull_request --pull=false --bind -e "$2" --secret-file "$3" -P "ubuntu-latest=$4" -j "$5"' _ \
            "$clone" "$sock" "$work/event.json" "$work/secrets" "$image" "$job" > "$work/$job.log" 2>&1; then
        echo "   pass"
    else
        echo "   FAIL (log tail)"
        tail -n 25 "$work/$job.log" | sed 's/^/   | /'
        fail=1
    fi
done
exit "$fail"
