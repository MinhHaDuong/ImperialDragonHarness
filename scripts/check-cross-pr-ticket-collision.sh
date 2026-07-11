#!/usr/bin/env bash
# check-cross-pr-ticket-collision.sh — CI gate against the optimistic-ID trap.
#
# The optimistic ID allocation trap (git-erg#282, wontfix) bites across *open
# PRs*: `erg new` scans only the local checkout, so two branches can hand out the
# same ticket ID. Per-branch `erg check` and the `validate-tickets` CI job both
# pass — each branch's IDs are unique within itself — and the duplicate only
# materializes on `main` after the second PR merges, by which point the first has
# already landed. This script closes that gap: for the PR under test it lists the
# ticket IDs it ADDS and fails if any is also added by another OPEN PR.
#
# A ticket added relative to the base branch cannot already exist on the base by
# construction (that is what `--diff-filter=A` against the base means), so the
# base-branch collision the ticket mentions is covered for free; the live gap is
# sibling open PRs, which this script enumerates.
#
# Forge coupling is confined to two calls, each marked `# harness-extension-point`
# (the isolation idiom used in skills/merge/erg-pr-merge): listing open PRs and
# fetching a PR's changed files. Everything else is forge-agnostic git + text.
#
# Environment (all optional; defaults suit GitHub Actions `pull_request`):
#   BASE_REF        base ref to diff against          (default: origin/main)
#   SELF_PR_NUMBER  this PR's number, excluded from the sibling scan
#
# Exit 0: no collision (or no ticket files added — fast path, no forge calls).
# Exit 1: a ticket ID this PR adds is also added by an open PR. Message names the
#         colliding PR(s) and suggests the next free ID.

set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
SELF_PR="${SELF_PR_NUMBER:-}"

# Keep only top-level tickets/NNNN-*.erg — never tickets/closed/... (a PR that
# merely closes a ticket "adds" the archived copy under closed/, which is not a
# new ID claim). The anchored regex also drops any stray non-ticket path.
ticket_ids_from_paths() {  # reads filenames on stdin, prints 4-digit IDs
    grep -E '^tickets/[0-9]{4}-.*\.erg$' \
        | sed -E 's|^tickets/([0-9]{4})-.*|\1|' \
        | sort -u
}

# ── this PR's newly-added ticket IDs (local git, no forge call) ───────────────
OWN_IDS=$(
    git diff --diff-filter=A --name-only "${BASE_REF}...HEAD" -- tickets/ \
        | ticket_ids_from_paths
) || true

if [[ -z "$OWN_IDS" ]]; then
    echo "cross-pr-collision: this PR adds no ticket files — nothing to check."
    exit 0
fi

echo "cross-pr-collision: this PR adds ticket ID(s): $(echo "$OWN_IDS" | tr '\n' ' ')"

# ── enumerate sibling open PRs (forge-specific) ───────────────────────────────
# harness-extension-point: GitHub CLI — swap this block for another forge's API.
SIBLINGS_JSON=$(gh pr list --state open --json number,headRefName) # harness-extension-point

# Map each sibling PR number -> the ticket IDs it adds, collision-checking as we go.
collision=0

while IFS=$'\t' read -r pr_number pr_branch; do
    [[ -z "$pr_number" ]] && continue
    [[ -n "$SELF_PR" && "$pr_number" == "$SELF_PR" ]] && continue

    # harness-extension-point: GitHub CLI — fetch this PR's changed files.
    # Fail-open by design (hygiene gate; renumber-on-merge stays the backstop),
    # but say so — a silent skip would look identical to a clean pass in CI logs.
    if ! sib_files=$(
        gh api "repos/{owner}/{repo}/pulls/${pr_number}/files" --paginate \
            --jq '.[] | select(.status=="added") | .filename' 2>/dev/null
    ); then
        echo "cross-pr-collision: WARNING — could not fetch PR #${pr_number}'s files; check incomplete for that PR." >&2
        continue
    fi
    sib_ids=$(ticket_ids_from_paths <<< "$sib_files") || true
    [[ -z "$sib_ids" ]] && continue

    # Intersection of OWN_IDS and this sibling's added IDs. An empty $shared
    # feeds the loop one blank line, which the [[ -z ]] guard skips.
    shared=$(comm -12 <(echo "$OWN_IDS") <(echo "$sib_ids") || true)
    while IFS= read -r id; do
        [[ -z "$id" ]] && continue
        echo "COLLISION: ticket ID ${id} is also added by open PR #${pr_number} (branch ${pr_branch})." >&2
        collision=$((collision + 1))
    done <<< "$shared"
done < <(echo "$SIBLINGS_JSON" | jq -r '.[] | [.number, .headRefName] | @tsv')

if [[ "$collision" -ne 0 ]]; then
    # Only needed on failure — don't spawn erg on the clean path.
    next_id=$(tickets/erg next-id 2>/dev/null || echo "(run ./tickets/erg next-id)")
    echo "" >&2
    echo "Renumber your ticket(s) to a free ID and fix cross-references (git mv)." >&2
    echo "Next free ID on this branch: ${next_id}" >&2
    exit 1
fi

echo "cross-pr-collision: no open PR claims the same ticket ID(s) — OK."
exit 0
