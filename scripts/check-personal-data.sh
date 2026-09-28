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
BARE_HOSTS_PAT='ouvaton''\.coop|your-storageshare''\.de'
ALIAS_PAT='ods''\.services'
KEYRING_PAT='secret-tool'' lookup'' e-source-uid|app-password'' at'' .*keychain'
NET_PAT='ufw.*Net''Bird|Net''Bird.*ufw'
NAMES_PAT='Aristide''-Briand|109''694|cdim''-immo|Me'' MOROT|Me'' Orhon|Mme'' Xiao'
PATTERN="${HOSTS_PAT}|${BARE_HOSTS_PAT}|${ALIAS_PAT}|${KEYRING_PAT}|${NET_PAT}|${NAMES_PAT}"

fail=0
for target in "${TARGETS[@]}"; do
    [ -e "$target" ] || { echo "WARN: $target not found" >&2; continue; }
    # Explicit files are always scanned; directories inside a git work tree
    # are scanned over TRACKED files only (git-ignored local session
    # transcripts and caches under projects/ are not committable data).
    if [ -f "$target" ]; then
        matches=$(grep -InE "$PATTERN" "$target" 2>/dev/null || true)
    elif git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
         [ -n "$(git ls-files -- "$target" 2>/dev/null | head -1)" ]; then
        matches=$(git ls-files -z -- "$target" | xargs -0 -r grep -InE "$PATTERN" 2>/dev/null || true)
    else
        matches=$(grep -rnIE "$PATTERN" "$target" 2>/dev/null || true)
    fi
    while IFS= read -r match; do
        [ -z "$match" ] && continue
        echo "FAIL [tier-2 personal data]: $match"
        fail=1
    done <<< "$matches"
done

if [ "$fail" -eq 0 ]; then
    echo "OK: no tier-2 personal data found"
fi
exit $fail
