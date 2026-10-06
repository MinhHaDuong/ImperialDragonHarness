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
work=$(mktemp -d)
# shellcheck source=../ci-local/common.sh
. "$here/common.sh"
trap 'stop_service; rm -rf "$work"' EXIT
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

start_service
ensure_image

# act's default copy drops .git, so run from a real clone bind-mounted into the
# container. Origin points at the forge so `gh` resolves {owner}/{repo}.
origin=$(git remote get-url origin)
clone="$work/clone"
git clone --quiet --no-hardlinks "$root" "$clone"
git -C "$clone" remote set-url origin "$origin"
git -C "$clone" fetch --quiet origin

# Find this checkout's PR by the commit it points at, not by branch name: a
# local branch is often pushed under another name, and an unrecognised PR would
# then count as its own sibling in the collision job.
open_prs=$(gh pr list --state open --json number,baseRefName,headRefOid)
head_sha=$(git rev-parse HEAD)
pr=$(jq -r --arg sha "$head_sha" '[.[] | select(.headRefOid == $sha)][0].number // empty' <<< "$open_prs")
base=$(jq -r --arg sha "$head_sha" '[.[] | select(.headRefOid == $sha)][0].baseRefName // empty' <<< "$open_prs")
if [ -z "$pr" ] || [ -z "$base" ]; then
    echo "local-ci: HEAD is not the head of an open PR; assuming base main, so every open PR counts as a sibling" >&2
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
        # Counts let a pass be compared with the forge's, not just trusted.
        grep -E '[0-9]+ passed' "$work/$job.log" | tail -n 1 | sed 's/^.*| /   /' || true
    else
        echo "   FAIL (log tail)"
        tail -n 25 "$work/$job.log" | sed 's/^/   | /'
        fail=1
    fi
done
exit "$fail"
