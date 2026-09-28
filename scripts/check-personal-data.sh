#!/usr/bin/env bash
# Guard against tier-2 personal data (access topology) in the public harness.
# T2 = mail/IMAP/SMTP hosts, login aliases, keyring-extraction procedures,
# credential-store inventories. T2 lives in ~/.config/harness/private/ (never
# committed) — see docs/2026-09-28-personal-data-tiers.md.
# Usage: check-personal-data.sh [file-or-dir ...]   (default: skills/ projects/ docs/)
set -euo pipefail

if [ $# -eq 0 ]; then
    TARGETS=(skills/ projects/ docs/)
else
    TARGETS=("$@")
fi

# Patterns are built by adjacent-string concatenation so that this file (and
# the CI fixtures that exercise it) never contains the literal T2 strings and
# does not flag itself.
HOSTS_PAT='(imap|smtp)\.(cnrs''\.fr|ouvaton''\.coop|centre-cired''\.fr|orange''\.fr)'
ALIAS_PAT='ods''\.services'
KEYRING_PAT='secret-tool'' lookup'' e-source-uid'
PATTERN="${HOSTS_PAT}|${ALIAS_PAT}|${KEYRING_PAT}"

fail=0
for target in "${TARGETS[@]}"; do
    [ -e "$target" ] || { echo "WARN: $target not found" >&2; continue; }
    while IFS= read -r match; do
        [ -z "$match" ] && continue
        echo "FAIL [tier-2 personal data]: $match"
        fail=1
    done < <(grep -rnIE "$PATTERN" "$target" 2>/dev/null || true)
done

if [ "$fail" -eq 0 ]; then
    echo "OK: no tier-2 personal data found"
fi
exit $fail
