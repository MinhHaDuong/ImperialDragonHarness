#!/usr/bin/env bash
# Guard (tickets 0939, 0945): project-.env values must not appear under xtrace.
# Every value is a recognisable fake sentinel in a disposable directory.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOADER="$REPO/scripts/bash-env.sh"
SENTINEL='XTRACE-PROJECT-SENTINEL-4KQ7Z'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
H="$TMP/home"
PROJECT="$TMP/project"
mkdir -p "$H" "$PROJECT"
printf 'SENTINEL_PROJECT=%s\n' "$SENTINEL" > "$PROJECT/.env"

FAIL=0
report() {
    printf '%-58s %s %s\n' "$1" "$2" "${3:-}"
    [ "$2" = PASS ] || FAIL=$((FAIL + 1))
}

trace_of() {
    ( cd "$PROJECT" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$1" \
        bash -x -c ':' 2>&1 >/dev/null ) || true
}

# Positive control: same already-expanded export shape, without the guard.
cat > "$TMP/unguarded.sh" <<'EOF'
while IFS= read -r line; do
    key="${line%%=*}"
    value="${line#*=}"
    export "$key=$value"
done < "$PWD/.env"
EOF
n="$(trace_of "$TMP/unguarded.sh" | grep -c "$SENTINEL" || true)"
if [ "$n" -gt 0 ]; then
    report "0. positive control: unguarded export leaks" PASS "($n traced lines)"
else
    report "0. positive control: unguarded export leaks" FAIL \
        "probe is BLIND — the result below is worthless"
fi

real_trace="$(trace_of "$LOADER")"
if grep -q "$SENTINEL" <<<"$real_trace"; then
    report "1. project .env value is silent under -x" FAIL "sentinel in trace"
else
    report "1. project .env value is silent under -x" PASS
fi

# Non-vacuity: absence from the trace matters only if the value was loaded.
loaded="$(cd "$PROJECT" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -c '[ "$SENTINEL_PROJECT" = "$1" ] && printf loaded' _ "$SENTINEL" \
    2>/dev/null)" || true
if [ "$loaded" = loaded ]; then
    report "2. non-vacuity: project value really loaded" PASS
else
    report "2. non-vacuity: project value really loaded" FAIL \
        "fixture did not load — case 1 proves nothing"
fi

n=$(( $(cd "$PROJECT" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -x -c 'echo caller-marker >/dev/null' 2>&1 | \
    grep -c 'caller-marker' || true) ))
if [ "$n" -gt 0 ]; then
    report "3. xtrace restored for the calling script" PASS
else
    report "3. xtrace restored for the calling script" FAIL "caller's trace lost"
fi

if (cd "$PROJECT" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
        bash -c 'case "$-" in *x*) exit 1 ;; esac; exit 0'); then
    report "4. xtrace stays off when caller had it off" PASS
else
    report "4. xtrace stays off when caller had it off" FAIL \
        "guard turned xtrace on, or loader exited non-zero"
fi

if [ "$FAIL" -eq 0 ]; then
    echo "OK — bash-env.sh does not trace project .env values"
else
    echo "FAILED — $FAIL check(s)"
fi
exit $((FAIL > 0 ? 1 : 0))
