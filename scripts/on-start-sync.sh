#!/bin/bash
set -euo pipefail
# Session-start repository upkeep, run as its own Claude SessionStart hook next
# to on-start-context.sh. Silent by contract: hook stdout is conversation
# context, and this half only mutates state. It needs a runtime-given project
# root (CLAUDE_PROJECT_DIR), so other runtimes and bare shells are a no-op.
exec >/dev/null 2>&1

[ -n "${CLAUDE_PROJECT_DIR:-}" ] && cd "$CLAUDE_PROJECT_DIR" || exit 0
_script_dir="$(cd "$(dirname "$0")" && pwd)"

# Activate project git hooks if a pre-commit hook exists
if [ -f hooks/pre-commit ]; then
    git config core.hooksPath hooks
fi

# Eager local-main sync (rules/git.md, "Local main syncs by ref").
# Backgrounded so an offline fetch can never stall session start; the script
# is ff-only and never touches dirty or diverged state, so racing the
# session's first git commands is safe. The report lands in
# <git-common-dir>/sync-local-main.last; the next session start surfaces it
# through on-start-context.sh if it needs attention.
# Write via tmp + mv: concurrent session starts share the common dir, and an
# atomic rename keeps the report whole (last-writer-wins, never interleaved).
_gcd=$(git rev-parse --git-common-dir 2>/dev/null) || _gcd=""
case "$_gcd" in /*|"") ;; *) _gcd="$PWD/$_gcd" ;; esac
if [ -n "$_gcd" ]; then
    ( { timeout 60 "$_script_dir/sync-local-main.sh" "$CLAUDE_PROJECT_DIR" \
          > "$_gcd/sync-local-main.last.$$" 2>&1 \
        && mv -f "$_gcd/sync-local-main.last.$$" "$_gcd/sync-local-main.last" \
        || rm -f "$_gcd/sync-local-main.last.$$"; } & )
fi
