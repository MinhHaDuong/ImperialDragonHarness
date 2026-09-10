#!/usr/bin/env bash
# Report merged PRs whose `**Ticket:**` close claim was never executed (ticket 0903).
#
# The close claim in a PR body is honoured by `erg-pr-merge`, not by the forge.
# Any other merge route — a bare forge-CLI merge, the forge's web UI, another
# machine, another session — lands the code and drops the claim with no output.
# `erg check` passes either way, so the dropped close and a clean merge leave
# identical evidence behind (git-erg PR #334, 2026-09-10: the fix for ticket
# 0276 sat on main while 0276 stayed open; a `/perch` pass found it by luck).
#
# WHY THIS IS NOT A REPLAY OF healthcheck STEP 9. That step reports
# `tickets.closed_unarchived` — tickets carrying a `Closed:` header that were
# never moved to `tickets/closed/`. It indexes on the header being PRESENT, so
# it is blind by construction to a ticket that was never closed at all: to it,
# such a ticket is indistinguishable from one still legitimately open. This
# script joins from the other side — merged PRs that claimed a close — which is
# the only side that can see it.
#
# WHY NOT REUSE THE SENTINEL. /roar step 2 advances its own sentinel as it logs
# telemetry, so by the time this runs the range is gone. A date window is
# self-contained and, unlike a git range, also covers merges made from another
# checkout that this one has not pulled.
set -euo pipefail

LIMIT=30
DAYS=7
while [ $# -gt 0 ]; do
    case "$1" in
        --limit) LIMIT="$2"; shift 2 ;;
        --days)  DAYS="$2";  shift 2 ;;
        -h|--help)
            echo "usage: check-close-claims.sh [--days N] [--limit N]"
            echo "  Reports merged PRs whose close claim never ran. Exit 1 if any."
            exit 0 ;;
        *) echo "check-close-claims: unknown argument '$1'" >&2; exit 2 ;;
    esac
done

if [ ! -d tickets ]; then
    echo "check-close-claims: no tickets/ directory — nothing to check."
    exit 0
fi
SINCE=$(date -u -d "${DAYS} days ago" +%Y-%m-%dT%H:%M:%SZ)

# ── The only forge-specific part, isolated here on purpose ────────────────────
# Everything below this function reasons over a JSON array of
# {number, title, body, mergedAt}. Porting to another forge means replacing
# these two calls and nothing else.

forge_available() {
    command -v gh >/dev/null 2>&1  # harness-extension-point
}

forge_merged_prs() { # <since-iso> <limit> → JSON array on stdout
    # One call. `body` populates on the list form (unlike `files`, which does
    # not — see tickets/AGENTS.md), so no per-PR query is needed here.
    gh pr list --state merged --limit "$2" \
        --json number,title,body,mergedAt \
        --jq "[.[] | select(.mergedAt >= \"$1\")]" 2>/dev/null  # harness-extension-point
}

if ! forge_available; then
    echo "check-close-claims: the forge CLI is not available, so merged PRs cannot be read." >&2
    echo "check-close-claims: this is NOT an all-clear." >&2
    exit 2
fi

PRS=$(forge_merged_prs "$SINCE" "$LIMIT") || PRS=""

if [ -z "$PRS" ]; then
    echo "check-close-claims: the forge query returned nothing." >&2
    echo "check-close-claims: cannot distinguish 'no merges' from 'could not look' — NOT an all-clear." >&2
    exit 2
fi

EXAMINED=$(printf '%s' "$PRS" | jq 'length')
CLAIMED=0
NOCLOSE=0
UNRECOGNISED=0
FINDINGS=0

# `ticket_state <id>` → archived | closed | open | absent
ticket_state() {
    local id="$1" f
    for f in tickets/closed/"$id"-*.erg tickets/closed/"$id".erg; do
        [ -e "$f" ] && { echo archived; return 0; }
    done
    for f in tickets/"$id"-*.erg tickets/"$id".erg; do
        if [ -e "$f" ]; then
            if grep -qE '^Closed:[[:space:]]*[^[:space:]]' "$f"; then
                echo closed
            else
                echo open
            fi
            return 0
        fi
    done
    echo absent
}

while IFS=$'\t' read -r num title body_b64; do
    [ -n "$num" ] || continue
    body=$(printf '%s' "$body_b64" | base64 -d 2>/dev/null || true)

    # Same acceptance as erg-pr-merge: **Ticket:** / **Ticket**: / Ticket:,
    # followed by tickets/NNNN. `Ticket-ref:` does not match (no colon straight
    # after "ticket"), and `Ticket: none` carries no tickets/ path.
    ids=$(printf '%s' "$body" | grep -oiP '^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+' | sort -u || true)
    if [ -z "$ids" ]; then
        # Not a claim. Separate a body that explicitly declares no close from
        # one this script simply did not recognise, so the two never share a
        # bucket — a growing UNRECOGNISED count is how regex drift becomes
        # visible instead of silently shrinking what gets checked.
        if printf '%s' "$body" | grep -qiP '^\*{0,2}ticket(-ref)?:?\*{0,2}:?\s*(none\b|tickets/)'; then
            NOCLOSE=$((NOCLOSE + 1))
        else
            UNRECOGNISED=$((UNRECOGNISED + 1))
        fi
        continue
    fi
    CLAIMED=$((CLAIMED + 1))

    for id in $ids; do
        case "$(ticket_state "$id")" in
            archived|closed) ;;
            open)
                echo "DROPPED: PR #${num} claims ticket ${id}, which has no Closed: header — ${title}"
                FINDINGS=$((FINDINGS + 1))
                ;;
            absent)
                echo "UNRESOLVED: PR #${num} claims ticket ${id}, and no tickets/${id}-*.erg exists here — renumbered, or this checkout is behind — ${title}"
                FINDINGS=$((FINDINGS + 1))
                ;;
        esac
    done
# Tab-joined with base64 for the body: a PR body is multi-line and would
# otherwise break the record. Title is last-but-one and cannot contain a tab.
done < <(printf '%s' "$PRS" | jq -r '.[] | [(.number|tostring), .title, (.body // "" | @base64)] | @tsv')

# The counts are the positive control: they say what was looked at, so a silent
# run cannot pass for an all-clear when nothing was examined. They also add up,
# which is the point — a gap between EXAMINED and the three buckets would mean
# this script is checking less than it appears to.
echo "check-close-claims: examined ${EXAMINED} PRs merged since ${SINCE}; ${CLAIMED} close claim(s), ${NOCLOSE} explicit no-close, ${UNRECOGNISED} unrecognised; ${FINDINGS} finding(s)."
if [ "$EXAMINED" = 0 ]; then
    echo "check-close-claims: zero PRs examined — widen --days/--limit before reading this as clean." >&2
fi
if [ "$UNRECOGNISED" -gt 0 ]; then
    # Observed on this repo, 2026-09-10: 3 of 40 wrote their marker as a code
    # span (`Ticket: none`), which the anchored regex does not reach. Harmless
    # while it only hides no-close markers; worth a look if the count climbs,
    # because the same anchoring would hide a backticked close claim too. The
    # regex deliberately matches erg-pr-merge's rather than being loosened: a
    # looser one would read the syntax EXAMPLES in this repo's own docs as
    # claims, and erg-pr-merge refuses a backticked claim loudly anyway.
    echo "check-close-claims: ${UNRECOGNISED} PR(s) carried no recognised Ticket line — see the note in this script before widening the regex." >&2
fi

[ "$FINDINGS" = 0 ] || exit 1
exit 0
