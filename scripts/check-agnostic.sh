#!/usr/bin/env bash
# Detect consumer-project assumptions in harness skills, rules, tickets, and scripts.
# Usage: check-agnostic.sh [dir ...]   (default: skills rules tickets scripts)
# Escape hatch: add  <!-- harness-extension-point -->  on the same or preceding line,
# or (for a `\`-continued multi-line command) on any of its continuation lines.
# `closed/` subdirs are skipped — closed tickets are frozen archives, not amended.
set -euo pipefail

if [ $# -eq 0 ]; then
    DIRS=(skills rules tickets scripts)
else
    DIRS=("$@")
fi

# Patterns checked everywhere (skills + tickets + scripts).
# Use class-level patterns — never hardcode a specific username, path, or project name.
GLOBAL_PATTERNS=(
    '/home/[a-z]'   # any absolute home path (use ~/.claude or $HOME instead)
    '/Users/[A-Z]'  # macOS equivalent
)

# Patterns checked in the prose that states harness doctrine (skills/ and rules/).
# Vendor-namespaced environment variables name the tool that currently provides a
# capability, so doctrine written around them rots when the tool does (workflow.md
# § "Writing Skills and Hooks"). Name the capability in the rule; if the concrete
# knob is worth recording, put it behind a harness-extension-point marker.
# Added 2026-07-27: rules/ was never scanned and no pattern covered vendor env
# names, so the first violation of this rule reached a merge gate unflagged.
PROSE_PATTERNS=(
    'CLAUDE_CODE_[A-Z_]'   # vendor-namespaced runtime knob; name the capability instead
)

# Patterns checked only in skills/ (ticket bodies may legitimately name consumer projects
# when documenting mis-filed or related work). NOT applied to rules/: rules/git.md
# documents forge mechanics concretely by design, and retrofitting the forge patterns
# there is a separate cleanup, not this gate's job.
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
    # Prose patterns apply wherever harness doctrine is written: skills/ and rules/
    case "$dir" in
        skills*|*/skills*|rules*|*/rules*)
            for pattern in "${PROSE_PATTERNS[@]}"; do
                check_pattern "$pattern" "$dir"
            done
            ;;
    esac
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
