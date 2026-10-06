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
# Exit 0 only if every selected guard caught its violation. One run produced an
# infrastructure failure on one guard while a local-ci.sh run shared the host;
# cause not established, so run them one at a time.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
here="$root/ci-local"
work=$(mktemp -d)
# shellcheck source=../ci-local/common.sh
. "$here/common.sh"
trap 'stop_service; rm -rf "$work"' EXIT
trap 'exit 130' INT TERM

for tool in act podman; do
    command -v "$tool" >/dev/null || { echo "local-ci-negative-controls: $tool not found" >&2; exit 2; }
done

start_service
ensure_image

git clone --quiet --no-hardlinks "$root" "$work/clone"
cd "$work/clone"
base=$(git rev-parse HEAD)
skill=$(find skills -name SKILL.md | head -1)
printf '{"pull_request":{"number":0,"base":{"ref":"main"}},"number":0}\n' > "$work/event.json"

inject() {
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
    cases=("$@")
else
    cases=(validate-tickets skill-lint agnostic-guard status-verb-guard personal-data-guard pipefail-guard grep-e-guard tab-ifs-guard pytest-guard)
fi

fail=0
for job in "${cases[@]}"; do
    git reset -q --hard "$base"
    git clean -qfdx
    inject "$job"
    git add -A
    git -c user.name=probe -c user.email=probe@example.invalid commit -q --no-verify -m "probe $job" \
        || { echo "$job: INJECTION PRODUCED NO CHANGE"; fail=1; continue; }
    if DOCKER_HOST="unix://$sock" act pull_request --pull=false --bind -e "$work/event.json" \
            -P "ubuntu-latest=$image" -j "$job" > "$work/$job.log" 2>&1; then
        echo "$job: NOT CAUGHT (job passed)"
        fail=1
    else
        step=$(grep -m1 -o 'Failure - Main .*' "$work/$job.log" | sed 's/ \[.*//' || true)
        if [ -n "$step" ]; then
            echo "$job: caught - $step"
        else
            echo "$job: INFRA FAILURE, not a verdict (log tail follows)"
            tail -n 15 "$work/$job.log" | sed 's/^/   | /'
            fail=1
        fi
    fi
done
exit "$fail"
