#!/usr/bin/env bash
# Ticket 0945: the BASH_ENV loader must not materialise user-level credentials
# in a fresh child's environment or trace. All values are fake sentinels.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOADER="$REPO/scripts/bash-env.sh"
TMP="$(mktemp -d)"
child=""
trap '[ -z "$child" ] || kill "$child" 2>/dev/null || true; rm -rf "$TMP"' EXIT

H="$TMP/home"
P="$TMP/project"
mkdir -p "$H/.claude" "$P"
cat > "$H/.claude/.env" <<'EOF'
ANTHROPIC_API_KEY=fake-anthropic-0945
OPENAI_API_KEY=fake-openai-0945
OPENROUTER_API_KEY=fake-openrouter-0945
HAL_ID=fake-hal-id-0945
HAL_PASSWORD=fake-hal-password-0945
KEYS=fake-provider
EOF

names='ANTHROPIC_API_KEY OPENAI_API_KEY OPENROUTER_API_KEY HAL_ID HAL_PASSWORD KEYS'
fail=0

fresh_env="$(cd "$P" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" bash -c env)"
for name in $names; do
    if grep -q "^${name}=" <<<"$fresh_env"; then
        echo "FAIL: fresh child carries $name" >&2
        fail=1
    else
        echo "PASS: fresh child omits $name"
    fi
done

# Observe a live descendant through /proc, not merely `env` output.
(cd "$P" && exec env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -c 'exec sleep 30') &
child=$!
for _ in $(seq 1 100); do
    [ "$(cat "/proc/$child/comm" 2>/dev/null || true)" = sleep ] && break
    sleep 0.01
done
[ "$(cat "/proc/$child/comm" 2>/dev/null || true)" = sleep ] || {
    echo "FAIL: child never reached the observable sleep state" >&2
    exit 1
}
proc_env="$(tr '\0' '\n' < "/proc/$child/environ")"
for name in $names; do
    if grep -q "^${name}=" <<<"$proc_env"; then
        echo "FAIL: /proc/$child/environ carries $name" >&2
        fail=1
    else
        echo "PASS: /proc child omits $name"
    fi
done
kill "$child" 2>/dev/null || true
wait "$child" 2>/dev/null || true
child=""

trace="$(cd "$P" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -x -c ':' 2>&1 >/dev/null)"
if grep -q 'fake-.*-0945' <<<"$trace"; then
    echo "FAIL: bash -x exposed a fake credential value" >&2
    fail=1
else
    echo "PASS: bash -x exposes no credential value"
fi

exit "$fail"
