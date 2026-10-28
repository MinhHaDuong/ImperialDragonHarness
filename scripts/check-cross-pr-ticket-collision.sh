#!/usr/bin/env bash
# check-cross-pr-ticket-collision.sh — CI gate against the optimistic-ID trap.
#
# `erg new` allocates max+1 across the store, sibling worktrees' drafts, and
# cached local/remote branch tips (a best-effort pass bounded at 200 ms, falling
# back to the worktree result with a warning). Unfetched refs, separate clones,
# and concurrent allocations can still produce the same ID. Per-branch
# `erg check` and `validate-tickets` cannot detect every such collision. This
# gate checks the IDs the PR ADDS against both the base tip and sibling OPEN PRs.
#
# Two collision surfaces are checked. The base tip: the added-files diff is
# taken against the merge-base, so an ID that landed on the base AFTER this
# branch diverged (via an already-merged claimant, absent from any open-PR scan)
# is invisible to it — the script therefore compares added IDs against the base
# tip's tickets/ directly, in plain git. And sibling OPEN PRs, via the forge.
#
# Forge coupling is confined to three scripts/forge.py calls (tickets 1318, 1325): `list --state
# open`, `origin` and `files <pr>`. Everything else is forge-agnostic git + text. The forge adapter owns
# the route: gh when the repository has an origin remote, none otherwise.
#
# Environment (all optional; defaults suit GitHub Actions `pull_request`):
#   BASE_REF        base ref to diff against          (default: origin/main)
#   SELF_PR_NUMBER  this PR's number (otherwise inferred from current branch)
#
# Exit 0: no collision (or no ticket files added — fast path, no forge calls).
# Exit 0 also: "skipped: no forge" when forge.py answers exit 3 (no origin remote) and the
#         base tip shows no collision; a base-tip collision still exits 1 (ticket 1325).
# Exit 2: the open-PR list could not be fetched (origin remote but no gh
#         auth/network), or self identity cannot be established — fails closed.
#         Inspection failure takes precedence over any base collision already
#         reported, and suppresses renumber advice until self identity is known.
# Exit 1: a ticket ID this PR adds is also on the base tip or added by an open PR. Message
#         names the rival file or PR(s) and suggests the next free ID.

set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
SELF_PR="${SELF_PR_NUMBER:-}"

renumber_and_fail() {  # only on failure — don't spawn erg on the clean path
    next_id=$(tickets/erg next-id 2>/dev/null || echo "(run ./tickets/erg next-id)")
    echo "" >&2
    echo "Renumber your ticket(s) to a free ID and fix cross-references (git mv)." >&2
    echo "Next free ID on this branch: ${next_id}" >&2
    exit 1
}

# Keep only top-level tickets/NNNN-*.erg — never tickets/closed/... (a PR that
# merely closes a ticket "adds" the archived copy under closed/, which is not a
# new ID claim). The anchored regex also drops any stray non-ticket path.
ticket_ids_from_paths() {  # reads filenames on stdin, prints 4-digit IDs
    grep -E '^tickets/[0-9]{4}-.*\.erg$' \
        | sed -E 's|^tickets/([0-9]{4})-.*|\1|' \
        | sort -u
}

# ── this PR's newly-added ticket files (local git, no forge call) ─────────────
# --no-renames pins a rename to delete(old)+add(new) regardless of git's
# similarity detection, so classification never depends on how much the
# rename edited the body.
OWN_PATHS=$(
    git diff --no-renames --diff-filter=A --name-only "${BASE_REF}...HEAD" -- tickets/ \
        | grep -E '^tickets/[0-9]{4}-.*\.erg$'
) || true
OWN_IDS=$(ticket_ids_from_paths <<< "$OWN_PATHS") || true

# Ticket files this PR deletes. A rename (slug fix) is delete(old)+add(new)
# with the same ID: the old path still on the base tip is this PR's own file,
# not a rival claim, and must not trip the base-tip check below.
OWN_DELETED=$(
    git diff --no-renames --diff-filter=D --name-only "${BASE_REF}...HEAD" -- tickets/ \
        | grep -E '^tickets/[0-9]{4}-.*\.erg$'
) || true

if [[ -z "$OWN_IDS" ]]; then
    echo "cross-pr-collision: this PR adds no ticket files — nothing to check."
    exit 0
fi

echo "cross-pr-collision: this PR adds ticket ID(s): $(echo "$OWN_IDS" | tr '\n' ' ')"

collision=0

# ── base-tip collision (local git, no forge call) ─────────────────────────────
# The merge-base diff above never sees a ticket that landed on the base tip
# after this branch diverged, and a merged claimant is invisible to the open-PR
# scan below. Compare added IDs against the base tip directly. A same-path hit
# is this PR's own file already landed (not a rival claim), so only a different
# filename carrying the same ID counts — and among those, a path this PR
# deletes is its own rename, not a rival.
BASE_TICKETS=$(git ls-tree -r --name-only "$BASE_REF" -- tickets/ \
    | grep -E '^tickets/[0-9]{4}-.*\.erg$' || true)
while IFS= read -r own_path; do
    [[ -z "$own_path" ]] && continue
    id=$(sed -E 's|^tickets/([0-9]{4})-.*|\1|' <<< "$own_path")
    rivals=$(grep -E "^tickets/${id}-" <<< "$BASE_TICKETS" | grep -vxF "$own_path" || true)
    if [[ -n "$rivals" && -n "$OWN_DELETED" ]]; then
        # drop base-tip paths this PR itself deletes (rename, not a rival)
        rivals=$(comm -23 <(sort <<< "$rivals") <(sort <<< "$OWN_DELETED") || true)
    fi
    [[ -z "$rivals" ]] && continue
    echo "COLLISION: ticket ID ${id} already exists on ${BASE_REF} as $(tr '\n' ' ' <<< "$rivals")(landed after this branch diverged)." >&2
    collision=$((collision + 1))
done <<< "$OWN_PATHS"

# ── enumerate sibling open PRs (through the forge adapter) ────────────────────
# forge.py list: exit 3 = no forge at all (typed NOOP; no sibling to collide with, so
# skip the scan legibly, keeping any base-tip collision), exit 2 = a forge exists and
# could not be read (fail closed).
FORGE_PY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/forge.py"
forge_rc=0
SIBLINGS_JSON=$(python3 "$FORGE_PY" list --state open --limit 100 2>/dev/null) || forge_rc=$?
if [[ "$forge_rc" -eq 3 ]]; then
    echo "cross-pr-collision: skipped: no forge (no origin remote), so no sibling PR to compare."
    [[ "$collision" -ne 0 ]] && renumber_and_fail
    exit 0
elif [[ "$forge_rc" -ne 0 ]]; then
    echo "cross-pr-collision: cannot list open PRs (no gh auth/network/GitHub remote)" >&2
    exit 2
fi

# ── infer self only when the caller supplied no explicit override ────────────
if [[ -z "$SELF_PR" ]]; then
    CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || true)
    if [[ -z "$CURRENT_BRANCH" ]]; then
        echo "cross-pr-collision: cannot establish self branch; set SELF_PR_NUMBER (no renumber recommendation)." >&2
        exit 2
    fi
    # Self is the head repository AND branch of this checkout's origin, never the
    # branch name alone (a fork may reuse it) nor cross_repository, which compares
    # head with base and so marks a fork checkout's own PR as foreign (ticket 1325).
    # Compared case-insensitively: GitHub owner/name are, and a clone may differ in case.
    if ! SOURCE_REPO=$(python3 "$FORGE_PY" origin 2>/dev/null) || [[ -z "$SOURCE_REPO" ]]; then
        echo "cross-pr-collision: cannot establish self repository; set SELF_PR_NUMBER (no renumber recommendation)." >&2
        exit 2
    fi
    SELF_MATCHES=$(jq -r --arg branch "$CURRENT_BRANCH" --arg repo "$SOURCE_REPO" '.[] | select(.branch == $branch and ((.head_repository // "") | ascii_downcase) == ($repo | ascii_downcase)) | .number' <<< "$SIBLINGS_JSON")
    if [[ $(grep -c . <<< "$SELF_MATCHES" || true) -gt 1 ]]; then
        echo "cross-pr-collision: ambiguous self PR for current repository/branch; set SELF_PR_NUMBER (no renumber recommendation)." >&2
        exit 2
    fi
    # No source match means every listed PR is a genuine sibling.
    SELF_PR="$SELF_MATCHES"
fi

while IFS=$'\t' read -r pr_number pr_branch; do
    [[ -z "$pr_number" ]] && continue
    [[ -n "$SELF_PR" && "$pr_number" == "$SELF_PR" ]] && continue

    # Fail-open by design (hygiene gate; renumber-on-merge stays the backstop),
    # but say so — a silent skip would look identical to a clean pass in CI logs.
    if ! sib_rows=$(python3 "$FORGE_PY" files "$pr_number" 2>/dev/null); then
        echo "cross-pr-collision: WARNING — could not fetch PR #${pr_number}'s files; check incomplete for that PR." >&2
        continue
    fi
    sib_files=$(jq -r '.[] | select(.status == "added") | .path' <<< "$sib_rows")
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
done < <(echo "$SIBLINGS_JSON" | jq -r '.[] | [.number, .branch] | @tsv')

[[ "$collision" -ne 0 ]] && renumber_and_fail

echo "cross-pr-collision: no open PR claims the same ticket ID(s) — OK."
exit 0
