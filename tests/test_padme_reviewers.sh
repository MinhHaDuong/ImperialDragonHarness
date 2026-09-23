#!/usr/bin/env bash
# Hermetic wrapper contract: a Padmé request owns its tunnel and sidecars.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/reviewers/42"
printf 'paid-seat-evidence\n' > "$work/reviewers/42/paid.findings"

cat > "$work/bin/ssh" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$TEST_SSH_ARGS"
exec sleep 30
STUB
cat > "$work/bin/curl" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
cat > "$work/bin/dispatcher" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
[[ "$REVIEWERS_FINDINGS_DIR" == "$TEST_ROOT/reviewers-padme" ]]
endpoint=$(sed -n 's/^[[:space:]]*endpoint: //p' "$REVIEWERS_PANEL")
[[ "$endpoint" =~ ^http://127\.0\.0\.1:([0-9]+)/v1$ ]]
[[ "${BASH_REMATCH[1]}" != 18080 ]]
[[ "$(cat "$TEST_ROOT/reviewers/42/paid.findings")" == paid-seat-evidence ]]
mkdir -p "$REVIEWERS_FINDINGS_DIR/42"
printf 'SUMMARY|findings=0|verdict=approve\n' > "$REVIEWERS_FINDINGS_DIR/42/local-padme-qwen.findings"
printf '%s\n' "$REVIEWERS_PANEL" > "$TEST_ROOT/generated-panel-path"
STUB
chmod +x "$work/bin/ssh" "$work/bin/curl" "$work/bin/dispatcher"

TEST_ROOT="$work" TEST_SSH_ARGS="$work/ssh.args" TMPDIR="$work" \
    PADME_REVIEWERS_DISPATCHER="$work/bin/dispatcher" PATH="$work/bin:$PATH" \
    "$root/skills/reviewers/padme-reviewers.sh" request 42

[[ "$(cat "$work/reviewers/42/paid.findings")" == paid-seat-evidence ]]
[[ -s "$work/reviewers-padme/42/local-padme-qwen.findings" ]]
[[ ! -e "$(cat "$work/generated-panel-path")" ]]
grep -q -- '-L' "$work/ssh.args"
echo 'PASS: Padmé request isolates findings, uses a fresh port, and cleans its roster'
