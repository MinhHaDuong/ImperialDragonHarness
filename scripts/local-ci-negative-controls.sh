#!/usr/bin/env bash
# Negative controls for scripts/local-ci.sh: inject one violation per guard into
# a throwaway clone of committed HEAD and require the matching job to FAIL at
# one of its own steps. A guard that stays green here is not a guard.
#
# A job that fails outside a workflow step (image, podman socket, checkout) is
# reported as an infrastructure failure, never as a catch: a first version of
# this check "caught" nine violations while no job had run at all.
#
# Usage: scripts/local-ci-negative-controls.sh [job ...]   (default: all nine guards)
# Exit 0 only if every selected guard caught its violation. The guards run in
# parallel, at most min(guards, nproc / 2) at once, each in its own clone. An
# earlier infrastructure failure beside a local-ci.sh run was a container-name
# clash between the two runners (ci-local/common.sh, tagged_workflow).
set -euo pipefail

root=$(git rev-parse --show-toplevel)
here="$root/ci-local"
work=$(mktemp -d)
# shellcheck source=../ci-local/common.sh
. "$here/common.sh"
trap 'stop_service; rm -rf "$work"' EXIT
trap 'kill_groups; kill $(jobs -p) 2>/dev/null || true; exit 130' INT TERM

for tool in act podman; do
    command -v "$tool" >/dev/null || { echo "local-ci-negative-controls: $tool not found" >&2; exit 2; }
done

start_service
ensure_image

base=$(git rev-parse HEAD)
printf '{"pull_request":{"number":0,"base":{"ref":"main"}},"number":0}\n' > "$work/event.json"
# Everything below derives from $base, not from the live checkout: a commit or an
# edit made while the guards run must not leak into a late case.
git show "$base:.github/workflows/CI.yml" > "$work/CI.base.yml"
tagged_workflow "$work/CI.base.yml" "$work/workflow.yml" "n$$"
snapshot="$work/snapshot"
git clone --quiet --no-hardlinks "$root" "$snapshot"
git -C "$snapshot" checkout --quiet --detach "$base"

# inject runs inside the case's clone.
inject() {
    local skill
    skill=$(find skills -name SKILL.md | head -1)
    case "$1" in
    validate-tickets)
        printf '%%erg 0.1\nTitle: dup\n' > tickets/0375-duplicate-id-probe.erg ;;
    skill-lint)
        sed -i '0,/^description:/s/^description:/descr1ption:/' "$skill" ;;
    agnostic-guard)
        # built from parts: the guard also scans this very script for the literal
        printf '/%s/someuser/projects/SomeProject\n' home >> "$skill" ;;
    status-verb-guard)
        echo '2026-05-01T10:00Z claude status closed — done' >> "$skill" ;;
    personal-data-guard)
        printf 'Login: minh.ha-duong@%s.services\n' ods > docs/zz-probe.md ;;
    pipefail-guard)
        printf '#!/bin/bash\necho hello\n' > scripts/zz-probe.sh ;;
    grep-e-guard)
        printf '#!/bin/bash\nset -euo pipefail\ngrep -qE %s file\n' "'\\bfoo\\b'" > scripts/zz-probe.sh ;;
    tab-ifs-guard)
        printf '#!/bin/bash\nset -euo pipefail\nwhile IFS=$%s read -r a b c; do :; done < f\n' "'\\t'" > scripts/zz-probe.sh ;;
    pytest-guard)
        printf 'def test_probe():\n    assert False\n' > tests/test_zz_probe.py ;;
    esac
}

if [ "$#" -gt 0 ]; then
    mapfile -t cases < <(dedupe_args "$@")
else
    cases=(validate-tickets skill-lint agnostic-guard status-verb-guard personal-data-guard pipefail-guard grep-e-guard tab-ifs-guard pytest-guard)
fi

# One case: its own clone, its verdict line in $work/<case>.out, 1 if not caught.
run_case() {
    local job=$1 clone="$work/clone-$1" step
    git clone --quiet --no-hardlinks "$snapshot" "$clone"
    git -C "$clone" checkout --quiet --detach "$base"
    cd "$clone"
    inject "$job"
    git add -A
    git -c user.name=probe -c user.email=probe@example.invalid commit -q --no-verify -m "probe $job" \
        || { echo "$job: INJECTION PRODUCED NO CHANGE" > "$work/$job.out"; return 1; }
    if DOCKER_HOST="unix://$sock" group_run "$job" act pull_request -W "$work/workflow.yml" --pull=false --bind -e "$work/event.json" \
            -P "ubuntu-latest=$image" -j "$job" > "$work/$job.log" 2>&1; then
        echo "$job: NOT CAUGHT (job passed)" > "$work/$job.out"
        return 1
    fi
    step=$(grep -m1 -o 'Failure - Main .*' "$work/$job.log" | sed 's/ \[.*//' || true)
    if [ -n "$step" ]; then
        echo "$job: caught - $step" > "$work/$job.out"
    else
        { echo "$job: INFRA FAILURE, not a verdict (log tail follows)"
          tail -n 15 "$work/$job.log" | sed 's/^/   | /'; } > "$work/$job.out"
        return 1
    fi
}

n=$(concurrency "${#cases[@]}")
echo "local-ci-negative-controls: ${#cases[@]} guards, $n at a time"
run_pool "$n" run_case "${cases[@]}"
for job in "${cases[@]}"; do
    cat "$work/$job.out" 2>/dev/null || echo "$job: NO RESULT (case did not finish)"
done
exit "$pool_failed"
