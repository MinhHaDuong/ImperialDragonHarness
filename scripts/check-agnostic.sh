#!/usr/bin/env bash
# Detect consumer-project assumptions in harness skills and tickets.
# Usage: check-agnostic.sh [dir ...]   (default: skills tickets scripts)
# Escape hatch: add  <!-- harness-extension-point -->  on the same or preceding line,
# or (for a `\`-continued multi-line command) on any of its continuation lines.
# `closed/` subdirs are skipped — closed tickets are frozen archives, not amended.
set -euo pipefail

if [ $# -eq 0 ]; then
    DIRS=(skills tickets scripts)
else
    DIRS=("$@")
fi

# Patterns checked everywhere (skills + tickets).
# Use class-level patterns — never hardcode a specific username, path, or project name.
GLOBAL_PATTERNS=(
    '/home/[a-z]'   # any absolute home path (use ~/.claude or $HOME instead)
    '/Users/[A-Z]'  # macOS equivalent
)

# Patterns checked only in skills/ (ticket bodies may legitimately name consumer projects
# when documenting mis-filed or related work).
# Note: consumer project *names* cannot be caught by static grep — the list would be
# instance-specific and go stale. Project names are caught by human review instead.
SKILL_PATTERNS=(
    'uv run pytest'   # stack-specific; skills must be stack-agnostic
    '\bgh '           # GitHub CLI; skills must be forge-agnostic
    'github\.com'     # GitHub URL; skills must be forge-agnostic
    '\(^\|[^.~/]\)scripts/[A-Za-z0-9_-]\+\.\(sh\|py\)'  # repo-relative script path; use ~/.claude/scripts/ or $HARNESS_DIR
)

fail=0

check_pattern() {
    local pattern="$1" dir="$2"
    [ -d "$dir" ] || { echo "WARN: directory not found: $dir" >&2; return; }
    while IFS= read -r match; do
        [ -z "$match" ] && continue
        file="${match%%:*}"
        rest="${match#*:}"
        lineno="${rest%%:*}"
        line="${rest#*:}"
        prev=""
        if [ "$lineno" -gt 1 ]; then
            prev=$(sed -n "$((lineno - 1))p" "$file")
        fi
        if echo "$line $prev" | grep -q 'harness-extension-point'; then
            continue
        fi
        # Multi-line command: if the flagged line ends in a `\` continuation,
        # scan forward across the continued lines. A marker anywhere in the same
        # logical command (its natural home is the closing continuation line)
        # exempts the whole command.
        if printf '%s' "$line" | grep -q '\\[[:space:]]*$'; then
            scan=$lineno
            marked=0
            while :; do
                scan=$((scan + 1))
                cont=$(sed -n "${scan}p" "$file")
                [ -z "$cont" ] && [ "$scan" -gt "$lineno" ] && break
                if echo "$cont" | grep -q 'harness-extension-point'; then
                    marked=1
                    break
                fi
                printf '%s' "$cont" | grep -q '\\[[:space:]]*$' || break
            done
            [ "$marked" -eq 1 ] && continue
        fi
        echo "VIOLATION [$pattern]: $file:$lineno: $line"
        fail=1
    done < <(grep -rn --exclude-dir=closed "$pattern" "$dir" 2>/dev/null || true)
}

for dir in "${DIRS[@]}"; do
    for pattern in "${GLOBAL_PATTERNS[@]}"; do
        check_pattern "$pattern" "$dir"
    done
done

for dir in "${DIRS[@]}"; do
    # Skill patterns only apply to skills directories
    case "$dir" in
        skills*|*/skills*)
            for pattern in "${SKILL_PATTERNS[@]}"; do
                check_pattern "$pattern" "$dir"
            done
            ;;
    esac
done

exit $fail
