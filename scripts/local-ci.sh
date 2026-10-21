#!/usr/bin/env bash
# Run the repository's CI workflow locally, job by job, with `act` in podman.
#
# The workflow file stays the single definition of the checks; this script only
# supplies what a forge runner would: a clean clone, a runner image, an event
# and, when a forge is reachable, a token. CI.yml runs under workflow_dispatch,
# its trigger that needs no push (it has no pull_request trigger, ticket 1174);
# ticket-collision.yml, when present, runs under a pull_request event. Usage:
#
#   scripts/local-ci.sh [job ...]     # default: every job of both workflows
#
# What is tested: the COMMITTED HEAD of the current checkout, cloned fresh. An
# uncommitted change is not tested (a warning says so). The forge tests the
# merge of the PR into its base; this tests the branch head alone.
#
# For a configured workflow run, the first output line names the UTC time, the
# actor and the host. The actor is the OS user unless LOCAL_CI_ACTOR is set; a
# caller that is an agent should set it to the agent's identity. It is stated,
# not authenticated: the aim is that a run can be traced, not that it can be
# proved.
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
# -j it is given, hence one invocation per job. Jobs run in parallel, at most
# min(jobs, nproc / 2) at once (LOCAL_CI_CONCURRENCY overrides), each in its own
# clone and under a per-runner workflow name so that two runners on one host
# cannot collide on a container name (ci-local/common.sh).
set -euo pipefail

workflow=.github/workflows/CI.yml
collision_workflow=.github/workflows/ticket-collision.yml
root=$(git rev-parse --show-toplevel)
# A repository with no workflow has intentionally opted out of CI. Check this
# before project-local runner files or container tools are needed.
if ! git -C "$root" cat-file -e "HEAD:$workflow" 2>/dev/null; then
    echo "local-ci: SKIP — no $workflow at HEAD; no CI checks were run (exit 3, not a pass)."
    exit 3
fi

here="$root/ci-local"
if [ ! -r "$here/common.sh" ]; then
    echo "local-ci: ci-local/common.sh is missing for a repository with $workflow." >&2
    exit 2
fi
work=$(mktemp -d)
# shellcheck source=../ci-local/common.sh
. "$here/common.sh"
trap 'stop_service; rm -rf "$work"' EXIT
trap 'kill_groups; kill $(jobs -p) 2>/dev/null || true; exit 130' INT TERM

for tool in act podman; do
    command -v "$tool" >/dev/null || { echo "local-ci: $tool not found" >&2; exit 2; }
done
# An inherited .actrc can add options such as --dryrun that make every job "pass".
for rc in "$HOME/.actrc" "$root/.actrc"; do
    [ ! -e "$rc" ] || { echo "local-ci: refusing to run with $rc present (it can change act's behaviour)" >&2; exit 2; }
done

head=$(git rev-parse --short HEAD)
# Who, when, where, what: written to the output so a run can be traced.
echo "local-ci: $(date -u +%Y-%m-%dT%H:%MZ) ${LOCAL_CI_ACTOR:-$(id -un)}@$(hostname -s) testing committed HEAD $head of $(git rev-parse --abbrev-ref HEAD)"
if [ -n "$(git status --porcelain)" ]; then
    echo "local-ci: WARNING: uncommitted changes are NOT tested" >&2
fi
start_service
ensure_image

# act's default copy drops .git, so run from a real clone bind-mounted into the
# container. This clone is also the start-of-run snapshot every job clones from,
# so a commit made while the jobs run cannot change what a late job tests. Origin points at the forge so `gh` resolves {owner}/{repo}.
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

# Each workflow file with the event it is run under: one a workflow still
# accepts, or act selects none of its jobs.
workflows=("$workflow")
events=(workflow_dispatch)
if [ -e "$clone/$collision_workflow" ]; then
    workflows+=("$collision_workflow")
    events+=(pull_request)
fi

# The job list must be the workflows', not whatever discovery printed: a run
# that selects no jobs, or fewer than the workflows define, checks nothing.
# Each job maps to the index of its workflow, whose tagged copy is
# $work/workflow-<index>.yml.
declare -A wf_of=()
defined=
needs_forge=
for i in "${!workflows[@]}"; do
    wf=${workflows[$i]}
    wf_jobs=$(python3 -c 'import sys, yaml; print("\n".join(sorted(yaml.safe_load(open(sys.argv[1]))["jobs"])))' "$clone/$wf")
    needs_forge+=$(python3 -c 'import sys, json, yaml; j = yaml.safe_load(open(sys.argv[1]))["jobs"]; print("\n".join(k for k, v in j.items() if "secrets." in json.dumps(v)))' "$clone/$wf")$'\n'
    listing=$( (cd "$clone" && DOCKER_HOST="unix://$sock" act "${events[$i]}" -W "$wf" -l) 2> "$work/list.log") \
        || { echo "local-ci: act -l failed on $wf: $(cat "$work/list.log")" >&2; exit 2; }
    listed=$(awk 'NR>1 && NF {print $2}' <<< "$listing" | sort)
    if [ "$listed" != "$wf_jobs" ]; then
        echo "local-ci: act lists a different job set for $wf under ${events[$i]} than the workflow defines; refusing to report a pass" >&2
        echo "  workflow defines: $(tr '\n' ' ' <<< "$wf_jobs")" >&2
        echo "  act lists:        $(tr '\n' ' ' <<< "$listed")" >&2
        exit 2
    fi
    while IFS= read -r job; do
        [ -z "${wf_of[$job]+x}" ] || { echo "local-ci: job '$job' is defined in two workflows" >&2; exit 2; }
        wf_of[$job]=$i
    done <<< "$wf_jobs"
    defined+="$wf_jobs"$'\n'
    tagged_workflow "$clone/$wf" "$work/workflow-$i.yml" "r$$"
done
defined=${defined%$'\n'}
if [ "$#" -gt 0 ]; then
    mapfile -t jobs < <(dedupe_args "$@")
    for job in "${jobs[@]}"; do
        grep -qxF "$job" <<< "$defined" || { echo "local-ci: unknown job '$job'" >&2; exit 2; }
    done
else
    mapfile -t jobs <<< "$defined"
fi

# Each job runs in its own clone, in parallel, at most min(jobs, nproc / 2) at
# a time. A job writes its verdict to $work/<job>.rc and its log to
# $work/<job>.log; the report below is printed in job order, not finish order.

run_job() {
    local job=$1 jclone="$work/clone-$1" rc=0 i=${wf_of[$1]}
    if [ "$forge" -eq 0 ] && grep -qxF "$job" <<< "$needs_forge"; then
        echo skip > "$work/$job.rc"
        return 0
    fi
    git clone --quiet --no-hardlinks "$clone" "$jclone"
    if [ "$forge" -eq 1 ]; then
        git -C "$jclone" remote set-url origin "$origin"
        git -C "$jclone" fetch --quiet origin
    fi
    group_run "$job" timeout 1800 bash -c 'cd "$1" && shift && DOCKER_HOST="unix://$1" act "$7" -W "$6" --pull=false --bind -e "$2" --secret-file "$3" -P "ubuntu-latest=$4" -j "$5"' _ \
        "$jclone" "$sock" "$work/event.json" "$secrets" "$image" "$job" "$work/workflow-$i.yml" "${events[$i]}" > "$work/$job.log" 2>&1 || rc=$?
    echo "$rc" > "$work/$job.rc"
    rm -rf "$jclone"
}

n=$(concurrency "${#jobs[@]}")
echo "local-ci: ${#jobs[@]} jobs, $n at a time"
run_pool "$n" run_job "${jobs[@]}"

passed=()
failed=()
skipped=()
for job in "${jobs[@]}"; do
    echo "== $job"
    verdict=$(cat "$work/$job.rc" 2>/dev/null || echo missing)
    if [ "$verdict" = skip ]; then
        echo "   SKIPPED (uses the forge's secrets; no forge access)"
        skipped+=("$job")
    elif [ "$verdict" = 0 ]; then
        echo "   pass"
        # Counts let a pass be compared with the forge's, not just trusted.
        grep -E '[0-9]+ passed' "$work/$job.log" | tail -n 1 | sed 's/^.*| /   /' || true
        passed+=("$job")
    else
        echo "   FAIL (log tail)"
        tail -n 25 "$work/$job.log" 2>/dev/null | sed 's/^/   | /'
        failed+=("$job")
    fi
done

echo "local-ci: ${#passed[@]} passed, ${#failed[@]} failed, ${#skipped[@]} skipped${skipped[*]:+ (${skipped[*]})}"
[ "${#failed[@]}" -eq 0 ] || exit 1
if [ "${#skipped[@]}" -gt 0 ] && [ "${LOCAL_CI_STRICT:-0}" = 1 ]; then
    exit 1
fi
exit 0
