#!/usr/bin/env bash
# Reviewer-management dispatcher — pure I/O helper for the /reviewers skill.
# Case-switch dispatch; no plugin architecture.
#
# "Review is CI" (ticket 0205): each seat is a sandboxed CI-style reviewer
# job. `request` runs the 0217 seat-runner once per roster seat (one
# container per seat); `harvest` normalizes every seat's findings to the
# 0205 contract shape; `scorecard` appends a fixed-schema trial line.
#
# Containment is the seat-runner's OS sandbox (0217), NOT this script.
# This script holds no secrets; seat credentials load via BASH_ENV (0207).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${REVIEWERS_REPO:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
PANEL="${REVIEWERS_PANEL:-${SCRIPT_DIR}/panel.yml}"
# The 0217 seat-runner. Overridable so the test suite can stub it.
SEAT_RUNNER="${SEAT_RUNNER:-${SCRIPT_DIR}/../../scripts/seat-runner.sh}"
# Where per-seat findings land for harvest to collect (per merge request).
FINDINGS_DIR="${REVIEWERS_FINDINGS_DIR:-${TMPDIR:-/tmp}/reviewers}"

usage() {
    cat >&2 <<'EOF'
Usage: reviewers.sh <subcommand> [args]

Subcommands:
  list                          Show panel members and trial progress
  request <pr> [branch]         Run each seat (0217 seat-runner) over the MR
  harvest <pr>                  Normalize all seats' findings to one file
  scorecard <pr> <seat> <ver>   Append a fixed-schema trial line via erg note
EOF
    exit 1
}

# ── roster parsing ───────────────────────────────────────────────────────────
# Emit one pipe-separated record per seat: name kind status endpoint model
# login trial-ticket. Minimal block parser for the flat panel.yml schema;
# comment and blank lines are ignored, and an explicit `reviewers: []` yields
# nothing.
roster_records() {
    awk '
        /^[[:space:]]*#/        { next }
        /^reviewers:[[:space:]]*\[\][[:space:]]*$/ { exit }
        /^[[:space:]]*-[[:space:]]*name:/ {
            if (have) print rec(); have=1; name=val($0); kind=st=ep=mo=lg=tt=""; next
        }
        /^[[:space:]]+kind:/          { kind=val($0) }
        /^[[:space:]]+status:/        { st=val($0) }
        /^[[:space:]]+endpoint:/      { ep=val($0) }
        /^[[:space:]]+model:/         { mo=val($0) }
        /^[[:space:]]+login:/         { lg=val($0) }
        /^[[:space:]]+trial-ticket:/  { tt=val($0) }
        END { if (have) print rec() }
        function val(line,  v) { sub(/^[^:]*:[[:space:]]*/, "", line); gsub(/^[[:space:]]+|[[:space:]]+$/, "", line); return line }
        function rec() { return name"|"kind"|"st"|"ep"|"mo"|"lg"|"tt }
    ' "$PANEL" 2>/dev/null
}

panel_is_empty() { [ -z "$(roster_records)" ]; }

# ── PR → branch resolution (forge-specific; overridable for tests) ───────────
pr_branch() {  # $1 pr; honor an explicit override first
    local pr="$1"
    if [ -n "${REVIEWERS_PR_BRANCH:-}" ]; then echo "$REVIEWERS_PR_BRANCH"; return 0; fi
    gh pr view "$pr" --json headRefName --jq '.headRefName'  # harness-extension-point
}

# ── Forge reviewer request (forge-specific; swap for another forge) ──────────
request_forge_reviewer() {  # $1 pr, $2 bot login
    local pr="$1" login="$2"
    gh api --method POST \
        "repos/{owner}/{repo}/pulls/${pr}/requested_reviewers" \
        -f "reviewers[]=${login}" >/dev/null 2>&1  # harness-extension-point
}

subcmd="${1:-}"; shift || true

case "$subcmd" in
    list)
        if panel_is_empty; then echo "no reviewers configured"; exit 0; fi
        printf '%-18s %-12s %-9s %s\n' NAME KIND STATUS TRIAL-TICKET
        while IFS='|' read -r name kind st ep mo lg tt; do
            printf '%-18s %-12s %-9s %s\n' "$name" "$kind" "${st:-advisory}" "$tt"
        done < <(roster_records)
        ;;

    request)
        pr="${1:-}"; [ -n "$pr" ] || { echo "error: request requires a merge request identifier" >&2; exit 1; }
        if panel_is_empty; then echo "no reviewers configured"; exit 0; fi
        branch="${2:-$(pr_branch "$pr")}"
        [ -n "$branch" ] || { echo "error: could not resolve branch for MR #${pr}" >&2; exit 1; }
        dest="${FINDINGS_DIR}/${pr}"; mkdir -p "$dest"
        ran=0
        while IFS='|' read -r name kind st ep mo lg tt; do
            case "$kind" in
                forge-bot)
                    # Server-side reviewer, requested on demand — nothing
                    # fires without this explicit request (0206: no repo-wide
                    # auto-request lever). Fail-open like every other seat.
                    if [ -z "$lg" ]; then
                        echo "request: WARN forge-bot seat '${name}' has no login — skipped" >&2
                        continue
                    fi
                    if request_forge_reviewer "$pr" "$lg"; then
                        echo "request: forge-bot seat '${name}' requested (${lg}) on MR #${pr}" >&2
                    else
                        echo "request: WARN forge-bot seat '${name}' request failed (fail-open)" >&2
                    fi
                    ;;
                cli-agent|local-model)
                    # Per-seat fail-open: a seat that errors WARNs and the
                    # others proceed — one seat never blocks the verdict (0205).
                    if "$SEAT_RUNNER" --repo "$REPO_ROOT" --branch "$branch" \
                        --endpoint "$ep" --model "$mo" --out "${dest}/${name}.findings" \
                        >/dev/null 2>"${dest}/${name}.err"; then
                        echo "request: seat '${name}' ok → ${dest}/${name}.findings" >&2
                        ran=$((ran+1))
                    else
                        echo "request: WARN seat '${name}' failed (fail-open; see ${dest}/${name}.err)" >&2
                    fi
                    ;;
                *)
                    echo "request: WARN seat '${name}' has unknown kind '${kind}' — skipped" >&2
                    ;;
            esac
        done < <(roster_records)
        echo "request: ${ran} cli/model seat(s) ran for MR #${pr}" >&2
        ;;

    harvest)
        pr="${1:-}"; [ -n "$pr" ] || { echo "error: harvest requires a merge request identifier" >&2; exit 1; }
        dest="${FINDINGS_DIR}/${pr}"
        # No seats ran / empty panel → empty normalized output, exit 0.
        [ -d "$dest" ] || exit 0
        shopt -s nullglob
        for f in "$dest"/*.findings; do
            seat="$(basename "$f" .findings)"
            declare -A _seen=()
            while IFS= read -r line; do
                case "$line" in
                    FINDING\|*)
                        sev=$(sed -n 's/.*severity=\([^|]*\).*/\1/p' <<<"$line")
                        loc=$(sed -n 's/.*file=\([^|]*\).*/\1/p' <<<"$line")
                        rat=$(sed -n 's/.*rationale=\(.*\)$/\1/p' <<<"$line")
                        if [ -n "$sev" ] && [ -n "$loc" ]; then
                            if [ "$sev" = "verifiable-or-consider" ] || [ "$loc" = "PATH:LINE" ] || [ "$rat" = "ONE SENTENCE" ]; then
                                echo "harvest: DROP template-echo from '${seat}': ${line}" >&2; continue
                            fi
                            key="${sev}|${loc}|${rat}"
                            if [ -n "${_seen[$key]:-}" ]; then
                                echo "harvest: DROP duplicate from '${seat}': ${line}" >&2; continue
                            fi
                            _seen[$key]=1
                            echo "${sev}: ${loc} — ${rat}  [${seat}]"
                        else
                            echo "harvest: WARN unparseable finding from '${seat}': ${line}" >&2
                        fi
                        ;;
                    SUMMARY\|*) : ;;
                    "") : ;;
                    *) echo "harvest: WARN non-contract line from '${seat}': ${line}" >&2 ;;
                esac
            done < "$f"
            unset _seen
        done
        ;;

    scorecard)
        pr="${1:-}"; seat="${2:-}"; verdict="${3:-}"
        [ -n "$pr" ] && [ -n "$seat" ] && [ -n "$verdict" ] || { echo "error: scorecard requires <pr> <seat> <verdict-summary>" >&2; exit 1; }
        # Resolve the seat's trial ticket from the roster.
        tt=""
        while IFS='|' read -r n k s e m l t; do [ "$n" = "$seat" ] && tt="$t"; done < <(roster_records)
        [ -n "$tt" ] || { echo "error: seat '${seat}' not in roster (no trial-ticket)" >&2; exit 1; }
        tid=$(sed -n 's#.*/\([0-9]\{4\}\)-.*#\1#p' <<<"$tt")
        # Fixed schema so 0205's integration review is evidence-based, not vibes.
        line="MR #${pr} seat=${seat} verdict: ${verdict}"
        ERG="${ERG:-${SCRIPT_DIR}/../../tickets/erg}"
        "$ERG" log "$tid" "claude note ${line}"
        ;;

    ""|--help|-h) usage ;;
    *) echo "error: unknown subcommand '${subcmd}'" >&2; usage ;;
esac
