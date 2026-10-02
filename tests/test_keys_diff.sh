#!/usr/bin/env bash
# Tests for scripts/keys-diff.sh (ticket 0937).
#
# keys-diff compares the local keystore with another host's by variable NAME
# and sha256[:12] FINGERPRINT only — never a value. Its whole reason to exist
# is that a diverging keystore is otherwise invisible until a fail-open
# consumer silently degrades, so the red step here IS the divergence case: a
# check that reports "all agree" on a diverging fleet proves only that it ran.
#
# NO REAL CREDENTIAL IS USED OR NEEDED ANYWHERE IN THIS SUITE. Every fixture
# value is an obviously-fake sentinel in a fake keystore under fake HOMEs; the
# real ~/.config/keys is never read, because KEYS_DIFF_LOCAL_DIR is set on
# every invocation, and the "remote" is a stub ssh running the real scanner
# against a second fake HOME.
#
# The stub ssh stands in for the network hop. It records its full argv (case 4
# pins the invocation shape), then execs the argv it was handed —
# `bash -s -- --scan` — against the fake REMOTE HOME, with the real
# scripts/keys-diff.sh arriving on stdin exactly as a real ssh would deliver
# it. TEST_SSH_MODE=dead emulates an unreachable host (exit 255).
#
# Hygiene this suite holds itself to, mirroring the script it tests: a
# failing assertion never prints a sentinel value — the leak assertion says
# THAT a value leaked, not which one (rules/coding-bash.md; the 2026-07-27
# incident). Asserted against stdout AND stderr.
#
# Suite-wide `export BASH_ENV=` is the 0359 exemption (as in
# tests/test_seat_runner.sh): children must not re-run the project .env
# loader. Ambient provider credentials are unset first so a stray echo in any
# stub prints an empty string, not a secret.
set -euo pipefail

unset OPENAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY DEEPSEEK_API_KEY \
      MISTRAL_API_KEY TAVILY_API_KEY ZOTERO_API_KEY ZOTERO_RW_API_KEY \
      HAL_ID HAL_PASSWORD
export BASH_ENV=

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/keys-diff.sh"
fail=0

ok()  { echo "PASS: $1"; }
bad() { echo "FAIL: $1" >&2; fail=$((fail + 1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

OUT="$WORK/out"
ERR="$WORK/err"
SSH_ARGS="$WORK/ssh-args"

# --- fixtures: two fake HOMEs, obviously-fake sentinels -----------------------
LOCAL_HOME="$WORK/home-local"
REMOTE_HOME="$WORK/home-remote"
mkdir -p "$LOCAL_HOME/.config/keys" "$REMOTE_HOME/.config/keys"

IDH_SENTINEL='fake-or-idh-sentinel-0937'
PI_SENTINEL='fake-or-pi-sentinel-0937'
ALBERT_SENTINEL='fake-albert-sentinel-0937'
DIV_SENTINEL='fake-or-divergent-sentinel-0937'
NEW_SENTINEL='fake-or-new-sentinel-0937'

printf 'OPENROUTER_API_KEY_IDH=%s\nOPENROUTER_API_KEY_PI=%s\n' \
    "$IDH_SENTINEL" "$PI_SENTINEL" > "$LOCAL_HOME/.config/keys/openrouter.env"
printf 'ALBERT_API_KEY=%s\n' "$ALBERT_SENTINEL" > "$LOCAL_HOME/.config/keys/albert.env"

# Remote (divergent) openrouter.env: the IDH name with a DIFFERENT value, the
# PI name absent, and a NEW name the local side lacks. No albert.env at all
# on the remote — one fixture exercises all four divergence kinds at once.
printf 'OPENROUTER_API_KEY_IDH=%s\nOPENROUTER_API_KEY_NEW=%s\n' \
    "$DIV_SENTINEL" "$NEW_SENTINEL" > "$REMOTE_HOME/.config/keys/openrouter.env"

# Expected fingerprints, precomputed from the sentinels in an env -i child:
# the assertion compares the script's output against the recipe it is
# supposed to implement, not against a fingerprint the script produced.
fp_sentinel() { env -i bash -c 'printf %s "$1" | sha256sum | cut -c1-12' _ "$1"; }
FP_IDH="$(fp_sentinel "$IDH_SENTINEL")"
FP_DIV="$(fp_sentinel "$DIV_SENTINEL")"

# --- stub ssh -----------------------------------------------------------------
mkdir -p "$WORK/bin"
cat > "$WORK/bin/ssh" <<'STUB'
#!/usr/bin/env bash
# Stub ssh for tests/test_keys_diff.sh: record the full argv, then play the
# remote side. Leading ssh options and the destination host are dropped the
# way a real ssh consumes them, and the remaining argv — `bash -s -- --scan`
# — is exec'd with the fake remote HOME while scripts/keys-diff.sh arrives on
# stdin. TEST_SSH_MODE=dead emulates an unreachable host (exit 255).
set -u
printf '%s\n' "$*" >> "$TEST_SSH_ARGS"
if [ "${TEST_SSH_MODE:-}" = "dead" ]; then
    printf 'stub ssh: host unreachable (test mode)\n' >&2
    exit 255
fi
while [ "$#" -gt 0 ]; do
    case "$1" in
        --) shift; break ;;
        -o|-F|-i|-l|-L|-p|-b|-D|-W|-e|-I|-J) shift 2 ;;
        -*) shift ;;
        *) break ;;
    esac
done
[ "$#" -gt 0 ] && shift
exec env -i HOME="$TEST_REMOTE_HOME" PATH="$PATH" "$@"
STUB
chmod +x "$WORK/bin/ssh"

# --- runner --------------------------------------------------------------------
# rc/OUT/ERR/SSH_ARGS are globals the cases read after the call.
rc=0
run_keys_diff() {  # $1 = KEYS_DIFF_SSH value, $2 = TEST_SSH_MODE
    : > "$SSH_ARGS"
    rc=0
    KEYS_DIFF_LOCAL_DIR="$LOCAL_HOME/.config/keys" \
    KEYS_DIFF_SSH="$1" \
    TEST_SSH_ARGS="$SSH_ARGS" \
    TEST_REMOTE_HOME="$REMOTE_HOME" \
    TEST_SSH_MODE="$2" \
    "$SCRIPT" testhost > "$OUT" 2> "$ERR" || rc=$?
}

out_has()   { grep -qF -- "$1" "$OUT"; }
out_lacks() { ! grep -qF -- "$1" "$OUT"; }
err_has()   { grep -qF -- "$1" "$ERR"; }

assert_no_sentinel_leak() {  # $1 = case label
    local hit=no s
    for s in "$IDH_SENTINEL" "$PI_SENTINEL" "$ALBERT_SENTINEL" \
             "$DIV_SENTINEL" "$NEW_SENTINEL"; do
        if grep -qF -- "$s" "$OUT" || grep -qF -- "$s" "$ERR"; then hit=yes; fi
    done
    if [ "$hit" = "no" ]; then
        ok "$1 — no fixture value reached stdout or stderr"
    else
        bad "$1 — a fixture value reached stdout or stderr (the very leak the script exists to prevent)"
    fi
}

# --- (0) the script exists and is executable -------------------------------------
if [ -x "$SCRIPT" ]; then
    ok "(0) keys-diff exists and is executable"
else
    bad "(0) keys-diff is missing or not executable: scripts/keys-diff.sh"
    echo "--- $(basename "$0"): $fail failing case(s) ---" >&2
    exit 1
fi

# --- (1) divergence: exit 1, every divergence kind named, no value -------------
run_keys_diff "$WORK/bin/ssh" live

if [ "$rc" -eq 1 ]; then
    ok "(1) a divergent keystore exits 1"
else
    bad "(1) a divergent keystore: expected exit 1, got $rc"
fi

if out_has "OPENROUTER_API_KEY_IDH" && out_has "fingerprint mismatch"; then
    ok "(1) the mismatching name is reported as a fingerprint mismatch"
else
    bad "(1) the fingerprint mismatch was not reported"
fi
if out_has "$FP_IDH" && out_has "$FP_DIV"; then
    ok "(1) both precomputed fingerprints appear in the mismatch line"
else
    bad "(1) the precomputed fingerprints did not both appear in the output"
fi
if out_has "OPENROUTER_API_KEY_PI" && out_has "defined only locally"; then
    ok "(1) a name present only locally is reported"
else
    bad "(1) the local-only name was not reported"
fi
if out_has "OPENROUTER_API_KEY_NEW" && out_has "defined only remotely"; then
    ok "(1) a name present only remotely is reported"
else
    bad "(1) the remote-only name was not reported"
fi
if out_has "albert.env" && out_has "missing remotely"; then
    ok "(1) a file present on one machine only is reported"
else
    bad "(1) the file missing remotely was not reported"
fi
assert_no_sentinel_leak "(1)"

# --- (2) agreement: exit 0, one agree line per compared file ---------------------
cp "$LOCAL_HOME/.config/keys/openrouter.env" "$REMOTE_HOME/.config/keys/openrouter.env"
cp "$LOCAL_HOME/.config/keys/albert.env" "$REMOTE_HOME/.config/keys/albert.env"
run_keys_diff "$WORK/bin/ssh" live

if [ "$rc" -eq 0 ]; then
    ok "(2) agreeing keystores exit 0"
else
    bad "(2) agreeing keystores: expected exit 0, got $rc"
fi
if out_has "agree: openrouter.env" && out_has "agree: albert.env"; then
    ok "(2) agreement prints one agree line per compared file, naming the file"
else
    bad "(2) the agree lines do not name every compared file"
fi
if out_lacks "mismatch"; then
    ok "(2) no divergence is reported on agreeing keystores"
else
    bad "(2) a divergence was reported on agreeing keystores"
fi
assert_no_sentinel_leak "(2)"

# --- (3) unreachable host: exit 2, loud, never reported as agreement ------------
run_keys_diff "$WORK/bin/ssh" dead

if [ "$rc" -eq 2 ]; then
    ok "(3) an unreachable host exits 2 (could-not-look), not 0 and not 1"
else
    bad "(3) an unreachable host: expected exit 2, got $rc"
fi
if out_lacks "agree"; then
    ok "(3) no agree line is printed when the remote could not be inspected"
else
    bad "(3) agreement was reported despite an unreachable host"
fi
if err_has "testhost"; then
    ok "(3) stderr names the host"
else
    bad "(3) stderr does not name the host"
fi
assert_no_sentinel_leak "(3)"

# --- (4) invocation shape ---------------------------------------------------------
# KEYS_DIFF_SSH is invoked UNQUOTED so the multi-word default word-splits;
# a two-word test value proves the split happens and that the option and the
# host both reach the recorded argv. Agreement fixtures from case (2), so a
# broken invocation cannot hide behind an expected divergence.
run_keys_diff "$WORK/bin/ssh -o BatchMode=yes" live
if [ "$rc" -eq 0 ]; then
    ok "(4) a multi-word KEYS_DIFF_SSH word-splits and the run still agrees"
else
    bad "(4) a multi-word KEYS_DIFF_SSH broke the invocation (exit $rc)"
fi
if grep -qF -- "-o BatchMode=yes" "$SSH_ARGS" && grep -qF -- "testhost" "$SSH_ARGS"; then
    ok "(4) the recorded ssh args carry the option and the host"
else
    bad "(4) the recorded ssh args do not carry the option and the host"
fi

echo "--- $(basename "$0"): $fail failing case(s) ---" >&2
exit "$fail"
