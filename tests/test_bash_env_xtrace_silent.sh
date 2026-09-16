#!/usr/bin/env bash
# Guard (ticket 0939): bash-env.sh must not trace credential values under xtrace.
#
# BASH_ENV is sourced at the startup of every non-interactive bash, and the
# loader moves credentials with two ordinary command forms — `source` under
# `set -a`, and `export "$DST=$VAL"`. `set -x` prints both WITH THE VALUE
# ALREADY EXPANDED, so a plain `bash -x script.sh` writes live keys to stderr.
# Six were exposed that way on 2026-09-16 before the guard went in.
#
# WHAT THIS TEST IS NOT. rules/coding-bash.md § "Unsetting a variable in the
# parent does not unset it in the child" has a different remedy for a different
# case: `export BASH_ENV=` / `env -i` make hermetic a child you CHOSE to
# isolate, ratcheted by test_bash_tests_are_hermetic.sh. Neither covers a
# `bash -x` where the loader MUST run because the script needs the keys, and
# neither reduces residency. This guard covers only the trace channel.
#
# NEVER RUN WITH A REAL KEY. Every value below is a fake sentinel in a fake
# HOME with a fake keystore. Verifying this with a live credential is how you
# leak it a second time (coding-bash.md, "fake sentinel loader").
#
# NON-VACUITY. A "sentinel absent from the trace" result has two causes and
# cannot by itself say which: the guard works, or the fixture never loaded
# anything. Case 3 asserts the sentinels really are exported, so cases 1-2 are
# measuring a loader that ran. Case 0 is the probe's own positive control: an
# unguarded loader must leak, or the grep is blind and every later zero is
# worthless.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOADER="$REPO/scripts/bash-env.sh"

# Recognisable, obviously-fake, and distinct per export path so a leak names
# which of the two it came through.
SENTINEL_WHOLE='XTRACE-SENTINEL-WHOLEFILE-4KQ7Z'
SENTINEL_SEL='XTRACE-SENTINEL-SELECTED-9MJ2W'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
H="$TMP/home"
mkdir -p "$H/.claude" "$H/.config/keys"

# Fake provider file: one variable for the bare (whole-file source) form, one
# for the SRC=DST selection form.
cat > "$H/.config/keys/fakeprov.env" <<EOF
FAKE_WHOLE_SECRET=$SENTINEL_WHOLE
FAKE_SRC_SECRET=$SENTINEL_SEL
EOF

# Trusted user .env selecting both forms.
cat > "$H/.claude/.env" <<'EOF'
KEYS=fakeprov,fakeprov:FAKE_SRC_SECRET=FAKE_SELECTED_DST
EOF

FAIL=0
report() { # report NAME VERDICT DETAIL — never prints a value
    printf '%-58s %s %s\n' "$1" "$2" "${3:-}"
    [ "$2" = PASS ] || FAIL=$((FAIL + 1))
}

# Spawn hermetically: env -i so nothing ambient can mask the fixture, and so
# test_bash_tests_are_hermetic.sh stays green. cwd is $TMP, which has no .env,
# so the project-level parse cannot interfere.
trace_of() { # trace_of LOADER_PATH -> stderr of `bash -x -c :`, stdout dropped
    ( cd "$TMP" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$1" \
        bash -x -c ':' 2>&1 >/dev/null ) || true
}

# --- Case 0: positive control. An unguarded loader MUST leak. ---------------
# Without this, a blind grep would report every case below as clean.
cat > "$TMP/unguarded.sh" <<'EOF'
set -a
source "$HOME/.config/keys/fakeprov.env"
set +a
EOF
n=$(trace_of "$TMP/unguarded.sh" | grep -c "$SENTINEL_WHOLE" || true)
if [ "$n" -gt 0 ]; then
    report "0. positive control: unguarded loader leaks" PASS "($n traced lines)"
else
    report "0. positive control: unguarded loader leaks" FAIL \
        "probe is BLIND — every result below is worthless"
fi

# --- Cases 1-2: the real loader must not trace either export path -----------
real_trace="$(trace_of "$LOADER")"

if grep -q "$SENTINEL_WHOLE" <<<"$real_trace"; then
    report "1. whole-file source path silent under -x" FAIL "sentinel in trace"
else
    report "1. whole-file source path silent under -x" PASS
fi

if grep -q "$SENTINEL_SEL" <<<"$real_trace"; then
    report "2. SRC=DST selection path silent under -x" FAIL "sentinel in trace"
else
    report "2. SRC=DST selection path silent under -x" PASS
fi

# --- Case 3: non-vacuity. The loader really did load both paths. ------------
# If this fails, cases 1-2 were measuring a loader that did nothing.
loaded="$( cd "$TMP" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -c '[ "$FAKE_WHOLE_SECRET" = "$1" ] && [ "$FAKE_SELECTED_DST" = "$2" ] \
             && printf both' _ "$SENTINEL_WHOLE" "$SENTINEL_SEL" 2>/dev/null )" || true
if [ "$loaded" = both ]; then
    report "3. non-vacuity: both paths still export" PASS
else
    report "3. non-vacuity: both paths still export" FAIL \
        "fixture did not load — cases 1-2 prove nothing"
fi

# --- Case 4: the guard restores xtrace for the calling script ---------------
# A guard that silenced the caller's own trace would be a regression, not a fix.
n=$(( $( cd "$TMP" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
    bash -x -c 'echo caller-marker >/dev/null' 2>&1 | grep -c 'caller-marker' || true ) ))
if [ "$n" -gt 0 ]; then
    report "4. xtrace restored for the calling script" PASS
else
    report "4. xtrace restored for the calling script" FAIL "caller's trace lost"
fi

# --- Case 5: xtrace off stays off, and exit status is clean ----------------
if ( cd "$TMP" && env -i HOME="$H" PATH="$PATH" BASH_ENV="$LOADER" \
        bash -c 'case "$-" in *x*) exit 1 ;; esac; exit 0' ); then
    report "5. xtrace stays off when caller had it off" PASS
else
    report "5. xtrace stays off when caller had it off" FAIL \
        "guard turned xtrace on, or loader exited non-zero"
fi

if [ "$FAIL" -eq 0 ]; then
    echo "OK — bash-env.sh does not trace credential values"
else
    echo "FAILED — $FAIL check(s)"
fi
exit $(( FAIL > 0 ? 1 : 0 ))
