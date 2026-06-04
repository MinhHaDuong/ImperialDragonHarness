#!/usr/bin/env bash
# Reviewer-management dispatcher — pure I/O helper for /reviewers skill.
# Case-switch dispatch; no plugin architecture.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PANEL="${SCRIPT_DIR}/panel.yml"

usage() {
    echo "Usage: reviewers.sh <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  list                          Show panel members and trial progress"
    echo "  request <pr>                  Fire all configured reviewers for a merge request"
    echo "  harvest <pr>                  Collect and normalize external findings"
    echo "  scorecard <pr> <verdict>      Append trial line to ticket log via erg note"
    exit 1
}

# Check if panel roster has any reviewers configured
panel_is_empty() {
    # Matches "reviewers: []" or a file with no entries after "reviewers:"
    if grep -qE '^reviewers:\s*\[\]' "$PANEL" 2>/dev/null; then
        return 0
    fi
    # Count non-comment, non-empty lines after "reviewers:" that start with "- "
    local count
    count=$(sed -n '/^reviewers:/,$ { /^  - /p }' "$PANEL" 2>/dev/null | wc -l)
    [ "$count" -eq 0 ]
}

subcmd="${1:-}"
shift || true

case "$subcmd" in
    list)
        if panel_is_empty; then
            echo "no reviewers configured"
            exit 0
        fi
        # Future: parse panel.yml and display table
        echo "no reviewers configured"
        ;;

    request)
        pr="${1:-}"
        if [ -z "$pr" ]; then
            echo "error: request requires a merge request identifier" >&2
            exit 1
        fi
        if panel_is_empty; then
            echo "no reviewers configured"
            exit 0
        fi
        # Future: iterate panel entries, fire each reviewer by kind
        # harness-extension-point
        echo "no reviewers configured"
        ;;

    harvest)
        pr="${1:-}"
        if [ -z "$pr" ]; then
            echo "error: harvest requires a merge request identifier" >&2
            exit 1
        fi
        if panel_is_empty; then
            # Empty normalized output — no findings
            exit 0
        fi
        # Future: collect findings from each reviewer, normalize to 0205 shape
        # harness-extension-point
        exit 0
        ;;

    scorecard)
        pr="${1:-}"
        verdict="${2:-}"
        if [ -z "$pr" ] || [ -z "$verdict" ]; then
            echo "error: scorecard requires <pr> and <verdict-summary>" >&2
            exit 1
        fi
        # Future: resolve the owning ticket from the MR, then:
        #   erg note <ticket-id> "MR #${pr} verdict: ${verdict}"
        # harness-extension-point
        echo "scorecard: stub — would log verdict for MR #${pr}: ${verdict}"
        exit 0
        ;;

    ""|--help|-h)
        usage
        ;;

    *)
        echo "error: unknown subcommand '${subcmd}'" >&2
        usage
        ;;
esac
