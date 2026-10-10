#!/usr/bin/env bash
# One-shot PR outcome (ticket 1082): erg-pr-status reads the forge ONCE and
# exits 0 merged, 1 failed, 2 pending, 3 unreadable. It never waits. A second
# part greps the merge tooling and the skills that call it for waiting
# constructs (sleep, pgrep -, --watch, timeout, retry loops).
set -euo pipefail
# Hermetic children (ticket 0875): see tests/test_bash_tests_are_hermetic.sh.
export BASH_ENV=

ROOT=$(cd "$(dirname "$0")/.." && pwd)
STATUS="$ROOT/skills/merge/erg-pr-status"
fail=0
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

[[ -x "$STATUS" ]] || { echo "FAIL: $STATUS missing or not executable"; exit 1; }

mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
# Canned gh: counts calls, prints STUB_VIEW_JSON for `pr view`.
echo "$*" >> "$STUB_CALLS"
if [[ "$1 $2" == "pr view" ]]; then
    [[ "${STUB_VIEW_FAIL:-0}" == "1" ]] && { echo "stub: could not resolve" >&2; exit 1; }
    printf '%s\n' "$STUB_VIEW_JSON"; exit 0
fi
echo "unexpected gh call: $*" >&2; exit 99
STUB
chmod +x "$WORK/bin/gh"

# check NAME EXPECTED_RC EXPECTED_WORD JSON
check() {
    local name=$1 want=$2 word=$3 json=$4 rc=0 out calls
    : > "$WORK/calls"
    out=$(PATH="$WORK/bin:$PATH" STUB_CALLS="$WORK/calls" STUB_VIEW_JSON="$json" \
          STUB_VIEW_FAIL="${STUB_VIEW_FAIL:-0}" bash "$STATUS" 42 2>&1) || rc=$?
    calls=$(wc -l < "$WORK/calls" | tr -d ' ')
    if [[ "$rc" -ne "$want" ]]; then
        echo "FAIL: $name: exit $rc, want $want ($out)"; fail=1
    elif [[ "$out" != *"$word"* ]]; then
        echo "FAIL: $name: output lacks '$word' ($out)"; fail=1
    elif [[ "$calls" -ne 1 ]]; then
        echo "FAIL: $name: $calls forge calls, want exactly 1"; fail=1
    else
        echo "PASS: $name -> exit $rc, one forge call"
    fi
}

check merged 0 merged '{"number":42,"state":"MERGED","statusCheckRollup":[],"autoMergeRequest":null}'
check pending-running 2 pending '{"number":42,"state":"OPEN","statusCheckRollup":[{"status":"IN_PROGRESS","conclusion":""},{"status":"COMPLETED","conclusion":"SUCCESS"}],"autoMergeRequest":{"mergeMethod":"MERGE"}}'
check pending-green-not-landed 2 pending '{"number":42,"state":"OPEN","statusCheckRollup":[{"status":"COMPLETED","conclusion":"SUCCESS"}],"autoMergeRequest":{"mergeMethod":"MERGE"}}'
check pending-no-checks-yet 2 pending '{"number":42,"state":"OPEN","statusCheckRollup":[],"autoMergeRequest":null}'
check failed-check 1 failed '{"number":42,"state":"OPEN","statusCheckRollup":[{"status":"COMPLETED","conclusion":"FAILURE"},{"status":"IN_PROGRESS","conclusion":""}],"autoMergeRequest":null}'
check failed-timed-out 1 failed '{"number":42,"state":"OPEN","statusCheckRollup":[{"status":"COMPLETED","conclusion":"TIMED_OUT"}],"autoMergeRequest":null}'
check closed-unmerged 1 closed '{"number":42,"state":"CLOSED","statusCheckRollup":[],"autoMergeRequest":null}'
# Positive control for the error branch: a forge read that fails must be
# distinguishable (exit 3) from every outcome above.
STUB_VIEW_FAIL=1 check unreadable 3 "could not read" 'x'

# ── no waiting constructs in the merge tooling or the skill text ─────────────
# erg-pr-merge keeps ONE bounded mergeability settle (settle_mergeable, ticket
# 0904); everything else must be free of waiting.
scan_files=(
    "$ROOT/skills/merge/erg-pr-status"
    "$ROOT/skills/merge/SKILL.md"
    "$ROOT/skills/raid/SKILL.md"
    "$ROOT/skills/roar/SKILL.md"
)
pat='(^|[^[:alnum:]_-])sleep[[:space:]]+[0-9$"]|pgrep -|--watch|(^|[[:space:]])timeout[[:space:]]+[0-9$]|(^|[[:space:];])(while|until)[^;]*;[[:space:]]*do'
for f in "${scan_files[@]}"; do
    if hits=$(grep -nE "$pat" "$f"); then
        echo "FAIL: waiting construct in ${f#"$ROOT"/}:"; echo "$hits"; fail=1
    else
        echo "PASS: no waiting construct in ${f#"$ROOT"/}"
    fi
done

# erg-pr-merge: no foreground watch, no timeout wrapper, no pgrep, no checks
# watcher; the only sleep is the one inside settle_mergeable.
M="$ROOT/skills/merge/erg-pr-merge"
code=$(grep -vE '^[[:space:]]*#' "$M")
for bad in '--watch' 'pgrep -' 'timeout 600' 'gh pr checks'; do
    if grep -qF -- "$bad" <<<"$code"; then
        echo "FAIL: erg-pr-merge still contains '$bad'"; fail=1
    fi
done
nsleep=$(grep -cE '^[[:space:]]*sleep[[:space:]]' <<<"$code" || true)
if [[ "$nsleep" -ne 1 ]]; then
    echo "FAIL: erg-pr-merge has $nsleep sleep call(s), want exactly 1 (settle_mergeable)"; fail=1
else
    echo "PASS: erg-pr-merge: single bounded settle sleep, no watch/pgrep/timeout"
fi

# Positive control: the scanner must fire on a known-bad sample.
printf 'while true; do sleep 5; gh pr checks --watch; done\n' > "$WORK/bad.sh"
if grep -qE "$pat" "$WORK/bad.sh"; then
    echo "PASS: scanner fires on a known-bad waiter (positive control)"
else
    echo "FAIL: scanner is blind to a known-bad waiter"; fail=1
fi

exit "$fail"
