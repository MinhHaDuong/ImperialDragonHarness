#!/usr/bin/env bash
# Run the repository's CI workflow locally, job by job, with `act` in podman.
#
# The workflow file stays the single definition of the checks; this script only
# supplies what a forge runner would: a clean clone, a runner image, a
# pull_request event and, when a forge is reachable, a token. Usage:
#
#   scripts/local-ci.sh [job ...]     # default: every job of the workflow
#
# What is tested: the COMMITTED HEAD of the current checkout, cloned fresh. An
# uncommitted change is not tested (a warning says so). The forge tests the
# merge of the PR into its base; this tests the branch head alone.
#
# Needs act and podman. The forge CLI (`gh`, authenticated) and an `origin`
# remote are optional: without them the jobs that read the forge's secrets are
# SKIPPED, and the summary says so; a skip is never a pass. Set
# LOCAL_CI_STRICT=1 to make a skip fail the run. When forge access exists, the
# jobs receive the user's `gh` token: acceptable while the only code that runs
# is the author's own.
#
# Exit status: 0 all selected jobs passed (skips allowed unless strict);
# 1 a job failed; 2 the setup or the job list is wrong; 3 the repository has no
# workflow at HEAD, so there is nothing to run. `act -j` honours only the last
# -j it is given, hence one invocation per job.
set -euo pipefail

workflow=.github/workflows/CI.yml
root=$(git rev-parse --show-toplevel)
here="$root/ci-local"
work=$(mktemp -d)
# shellcheck source=../ci-local/common.sh
. "$here/common.sh"
trap 'stop_service; rm -rf "$work"' EXIT
trap 'exit 130' INT TERM

for tool in act podman; do
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
# No workflow is a state to declare, not to guess at: say so and stop.
git cat-file -e "HEAD:$workflow" 2>/dev/null || {
    echo "local-ci: no $workflow at HEAD, so there is no CI to run. This is not a pass." >&2
    exit 3
}

start_service
ensure_image

# act's default copy drops .git, so run from a real clone bind-mounted into the
# container. Origin points at the forge so `gh` resolves {owner}/{repo}.
clone="$work/clone"
git clone --quiet --no-hardlinks "$root" "$clone"

# Forge access is optional: a remote, the CLI and a login, all three.
forge=0
if origin=$(git remote get-url origin 2>/dev/null) && command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    forge=1
    git -C "$clone" remote set-url origin "$origin"
    git -C "$clone" fetch --quiet origin
else
    echo "local-ci: no forge access (needs an origin remote, gh, and a gh login); jobs that use the forge's secrets will be skipped" >&2
fi

pr=0
base=main
secrets="$work/secrets"
: > "$secrets"
chmod 600 "$secrets"
if [ "$forge" -eq 1 ]; then
    # Find this checkout's PR by the commit it points at, not by branch name: a
    # local branch is often pushed under another name, and an unrecognised PR
    # would then count as its own sibling in the collision job.
    open_prs=$(gh pr list --state open --json number,baseRefName,headRefOid)
    head_sha=$(git rev-parse HEAD)
    found_pr=$(jq -r --arg sha "$head_sha" '[.[] | select(.headRefOid == $sha)][0].number // empty' <<< "$open_prs")
    found_base=$(jq -r --arg sha "$head_sha" '[.[] | select(.headRefOid == $sha)][0].baseRefName // empty' <<< "$open_prs")
    if [ -n "$found_pr" ] && [ -n "$found_base" ]; then
        pr=$found_pr
        base=$found_base
    else
        echo "local-ci: HEAD is not the head of an open PR; assuming base main, so every open PR counts as a sibling" >&2
    fi
    printf 'GITHUB_TOKEN=%s\n' "$(gh auth token)" > "$secrets"
fi
printf '{"pull_request":{"number":%s,"base":{"ref":"%s"}},"number":%s}\n' "$pr" "$base" "$pr" > "$work/event.json"

act_in_clone() { (cd "$clone" && DOCKER_HOST="unix://$sock" act pull_request "$@"); }

# The job list must be the workflow's, not whatever discovery printed: a run
# that selects no jobs, or fewer than the workflow defines, checks nothing.
defined=$(python3 -c 'import sys, yaml; print("\n".join(sorted(yaml.safe_load(open(sys.argv[1]))["jobs"])))' "$clone/$workflow")
needs_forge=$(python3 -c 'import sys, json, yaml; j = yaml.safe_load(open(sys.argv[1]))["jobs"]; print("\n".join(k for k, v in j.items() if "secrets." in json.dumps(v)))' "$clone/$workflow")
listing=$(act_in_clone -l 2> "$work/list.log") || { echo "local-ci: act -l failed: $(cat "$work/list.log")" >&2; exit 2; }
listed=$(awk 'NR>1 && NF {print $2}' <<< "$listing" | sort)
if [ "$listed" != "$defined" ]; then
    echo "local-ci: act lists a different job set than the workflow defines; refusing to report a pass" >&2
    echo "  workflow defines: $(tr '\n' ' ' <<< "$defined")" >&2
    echo "  act lists:        $(tr '\n' ' ' <<< "$listed")" >&2
    exit 2
fi
if [ "$#" -gt 0 ]; then
    jobs=("$@")
    for job in "${jobs[@]}"; do
        grep -qxF "$job" <<< "$defined" || { echo "local-ci: unknown job '$job'" >&2; exit 2; }
    done
else
    mapfile -t jobs <<< "$defined"
fi

passed=()
failed=()
skipped=()
for job in "${jobs[@]}"; do
    echo "== $job"
    if [ "$forge" -eq 0 ] && grep -qxF "$job" <<< "$needs_forge"; then
        echo "   SKIPPED (uses the forge's secrets; no forge access)"
        skipped+=("$job")
        continue
    fi
    git -C "$clone" reset -q --hard HEAD
    git -C "$clone" clean -qfdx
    if timeout 1800 bash -c 'cd "$1" && shift && DOCKER_HOST="unix://$1" act pull_request --pull=false --bind -e "$2" --secret-file "$3" -P "ubuntu-latest=$4" -j "$5"' _ \
            "$clone" "$sock" "$work/event.json" "$secrets" "$image" "$job" > "$work/$job.log" 2>&1; then
        echo "   pass"
        # Counts let a pass be compared with the forge's, not just trusted.
        grep -E '[0-9]+ passed' "$work/$job.log" | tail -n 1 | sed 's/^.*| /   /' || true
        passed+=("$job")
    else
        echo "   FAIL (log tail)"
        tail -n 25 "$work/$job.log" | sed 's/^/   | /'
        failed+=("$job")
    fi
done

echo "local-ci: ${#passed[@]} passed, ${#failed[@]} failed, ${#skipped[@]} skipped${skipped[*]:+ (${skipped[*]})}"
[ "${#failed[@]}" -eq 0 ] || exit 1
if [ "${#skipped[@]}" -gt 0 ] && [ "${LOCAL_CI_STRICT:-0}" = 1 ]; then
    exit 1
fi
exit 0
