#!/usr/bin/env bash
# Regression suite for scripts/check-cross-pr-ticket-collision.sh.
#
# The optimistic-ID trap (git-erg#282) bites across open PRs: two branches can
# add the same ticket ID and every per-branch check passes. This script fails a
# PR whose added ticket ID is also added by another open PR.
#
# Method mirrors tests/test_erg_pr_merge.sh: a self-contained temp repo, a `gh`
# stub first on PATH dispatching on "$1 $2", canned responses from STUB_* env
# vars, and the real script run against it. The `gh api ... --jq` call is stubbed
# to emit filenames directly (emulating gh's built-in jq), matching what the
# script's downstream pipe consumes.
#
# Cases:
#   (a) own PR + a sibling open PR both add tickets/0300-*.erg -> exit 1, and the
#       message names the sibling PR number.
#   (b) sibling adds a different ID (0301) -> exit 0.
#   (c) own PR adds no ticket file -> exit 0 AND gh is never invoked (fast path).
#   (d) sibling file fetch fails -> still exit 0 (fail-open) but a WARNING names
#       the skipped PR, so the degraded check is visible in CI logs.
#   (e) the same ID landed on the BASE TIP via an already-merged claimant
#       (different filename) after the branch diverged -> exit 1 naming the base;
#       the merge-base diff and the open-PR scan are both blind to this one.
#   (f) the PR's own file (same path) already sits on the base tip -> exit 0;
#       a same-path hit is not a rival claim.
#   (g) the PR RENAMES a base ticket (delete old slug + add new slug, same ID)
#       -> exit 0; the old path on the base tip is the PR's own file, not a
#       rival claimant.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPT="$REPO_ROOT/scripts/check-cross-pr-ticket-collision.sh"
ERG_BIN="$REPO_ROOT/tickets/erg"
fail=0

[[ -f "$SCRIPT" ]]  || { echo "FAIL: $SCRIPT not found"; exit 1; }
[[ -x "$ERG_BIN" ]] || { echo "FAIL: $ERG_BIN not found"; exit 1; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# ── gh stub: dispatch by subcommand, log every call, emit canned responses ────
STUBDIR="$WORK/bin"
mkdir -p "$STUBDIR"
cat > "$STUBDIR/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "${STUB_GH_LOG:-/dev/null}"
case "$1 $2" in
  "pr list")
    echo "$STUB_PR_LIST" ;;
  "api "*|"api")
    # Emulate `gh api ... --jq '...'`: emit the already-filtered filenames the
    # script's downstream pipe expects (one per line).
    [[ -n "${STUB_API_FAIL:-}" ]] && exit 1
    printf '%s\n' ${STUB_SIBLING_FILES:-} ;;
  *)
    echo "stub gh: unexpected: $*" >&2; exit 1 ;;
esac
STUB
chmod +x "$STUBDIR/gh"

# ── seed a standalone repo: base branch + a PR branch adding a ticket ─────────
# Sets globals: $REPO, $BASE (base branch), $BRANCH (PR branch).
seed_repo() {
    local name="$1"; shift          # remaining args: ticket IDs the PR adds
    REPO="$WORK/$name"
    git init -q "$REPO"
    git -C "$REPO" config user.email "test@example.com"
    git -C "$REPO" config user.name  "Test"
    git -C "$REPO" config commit.gpgsign false
    git -C "$REPO" config tag.gpgsign false
    mkdir -p "$REPO/tickets"
    cp "$ERG_BIN" "$REPO/tickets/erg"
    # a pre-existing base ticket so `erg next-id` has something to scan
    cat > "$REPO/tickets/0001-base.erg" <<'ERG'
%erg 0.1
Title: Base ticket
Created: 2026-06-18
Author: test

--- log ---
2026-06-18T00:00Z test created

--- body ---
## Context
Pre-existing on base.
ERG
    git -C "$REPO" add tickets
    git -C "$REPO" commit -q -m "init: base"
    git -C "$REPO" remote add origin "$REPO"
    git -C "$REPO" config receive.denyCurrentBranch ignore
    git -C "$REPO" fetch -q origin
    BASE=$(git -C "$REPO" branch --show-current)
    BRANCH="pr-$name"
    git -C "$REPO" switch -q -c "$BRANCH"
    local n
    for n in "$@"; do
        cat > "$REPO/tickets/${n}-own.erg" <<ERG
%erg 0.1
Title: Own ticket ${n}
Created: 2026-06-18
Author: test

--- log ---
2026-06-18T00:00Z test created

--- body ---
## Context
Added by this PR.
ERG
        git -C "$REPO" add "tickets/${n}-own.erg"
    done
    if [[ $# -gt 0 ]]; then
        git -C "$REPO" commit -q -m "add own tickets"
    fi
}

# runs the real script with cwd in the repo and gh stubbed first on PATH
run_check() {  # env STUB_PR_LIST, STUB_SIBLING_FILES, SELF_PR_NUMBER, STUB_GH_LOG
    ( cd "$REPO"
      PATH="$STUBDIR:$PATH" \
      BASE_REF="origin/$BASE" \
      SELF_PR_NUMBER="${SELF_PR_NUMBER:-}" \
      STUB_PR_LIST="${STUB_PR_LIST:-[]}" \
      STUB_SIBLING_FILES="${STUB_SIBLING_FILES:-}" \
      STUB_API_FAIL="${STUB_API_FAIL:-}" \
      STUB_GH_LOG="${STUB_GH_LOG:-/dev/null}" \
      bash "$SCRIPT" )
}

# ════════════════════════════════════════════════════════════════════════════
# Case (a): own PR and a sibling both add 0300 -> collision, exit 1, names PR
# ════════════════════════════════════════════════════════════════════════════
seed_repo colliding 0300
if out=$(SELF_PR_NUMBER=99 \
         STUB_PR_LIST='[{"number":99,"headRefName":"pr-colliding"},{"number":77,"headRefName":"pr-sibling"}]' \
         STUB_SIBLING_FILES='tickets/0300-sibling.erg' \
         run_check 2>&1); then
    echo "FAIL: colliding IDs should have exited non-zero"; echo "$out"; fail=1
else
    a_ok=1
    echo "$out" | grep -q '0300'      || { echo "  message lacks the colliding ID 0300"; a_ok=0; }
    echo "$out" | grep -q '#77'       || { echo "  message does not name sibling PR #77"; a_ok=0; }
    echo "$out" | grep -qi 'next'     || { echo "  message lacks a next-free-ID suggestion"; a_ok=0; }
    if (( a_ok )); then echo "PASS: collision fails, names the sibling PR and a next-free-ID suggestion"
    else echo "FAIL: collision message incomplete"; fail=1; fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Case (b): sibling adds a DIFFERENT id (0301) -> no collision, exit 0
# ════════════════════════════════════════════════════════════════════════════
seed_repo distinct 0300
if out=$(SELF_PR_NUMBER=99 \
         STUB_PR_LIST='[{"number":99,"headRefName":"pr-distinct"},{"number":77,"headRefName":"pr-sibling"}]' \
         STUB_SIBLING_FILES='tickets/0301-sibling.erg' \
         run_check 2>&1); then
    echo "PASS: distinct IDs pass (exit 0)"
else
    echo "FAIL: distinct IDs wrongly flagged as a collision"; echo "$out"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case (c): own PR adds no ticket file -> exit 0 without ever invoking gh
# ════════════════════════════════════════════════════════════════════════════
seed_repo noticket            # no ticket IDs -> PR branch adds a non-ticket file
echo "some change" > "$REPO/README-change.txt"
git -C "$REPO" add README-change.txt
git -C "$REPO" commit -q -m "non-ticket change"
GHLOG="$WORK/gh-c.log"; : > "$GHLOG"
if out=$(STUB_GH_LOG="$GHLOG" \
         STUB_PR_LIST='[{"number":77,"headRefName":"pr-sibling"}]' \
         run_check 2>&1); then
    if [[ -s "$GHLOG" ]]; then
        echo "FAIL: fast path invoked gh despite no ticket adds:"; cat "$GHLOG"; fail=1
    else
        echo "PASS: no ticket adds -> exit 0, gh never invoked (fast path)"
    fi
else
    echo "FAIL: no-ticket-add case should exit 0"; echo "$out"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case (d): sibling file fetch fails -> fail-open (exit 0) with a visible WARNING
# ════════════════════════════════════════════════════════════════════════════
seed_repo apifail 0300
if out=$(SELF_PR_NUMBER=99 \
         STUB_PR_LIST='[{"number":99,"headRefName":"pr-apifail"},{"number":77,"headRefName":"pr-sibling"}]' \
         STUB_API_FAIL=1 \
         run_check 2>&1); then
    if echo "$out" | grep -q 'WARNING' && echo "$out" | grep -q '#77'; then
        echo "PASS: fetch failure fails open with a WARNING naming PR #77"
    else
        echo "FAIL: fetch failure exit 0 but no WARNING naming the skipped PR"; echo "$out"; fail=1
    fi
else
    echo "FAIL: fetch failure should fail open (exit 0)"; echo "$out"; fail=1
fi

# Adds a ticket file to the BASE branch after the PR branch diverged, then
# refreshes origin/$BASE (the repo is its own origin) and returns to the branch.
land_on_base() {  # $1 = filename under tickets/
    git -C "$REPO" switch -q "$BASE"
    cat > "$REPO/tickets/$1" <<ERG
%erg 0.1
Title: Landed on base after divergence
Created: 2026-06-18
Author: test

--- log ---
2026-06-18T00:00Z test created

--- body ---
## Context
Merged claimant.
ERG
    git -C "$REPO" add "tickets/$1"
    git -C "$REPO" commit -q -m "merged claimant: $1"
    git -C "$REPO" fetch -q origin
    git -C "$REPO" switch -q "$BRANCH"
}

# ════════════════════════════════════════════════════════════════════════════
# Case (e): same ID landed on the base tip via a merged claimant -> exit 1
# ════════════════════════════════════════════════════════════════════════════
seed_repo basecol 0300
land_on_base "0300-merged-sibling.erg"
if out=$(SELF_PR_NUMBER=99 STUB_PR_LIST='[]' run_check 2>&1); then
    echo "FAIL: base-tip collision should have exited non-zero"; echo "$out"; fail=1
else
    e_ok=1
    echo "$out" | grep -q '0300'                  || { echo "  message lacks the colliding ID 0300"; e_ok=0; }
    echo "$out" | grep -q '0300-merged-sibling'   || { echo "  message does not name the base-tip rival file"; e_ok=0; }
    echo "$out" | grep -qi 'next'                 || { echo "  message lacks a next-free-ID suggestion"; e_ok=0; }
    if (( e_ok )); then echo "PASS: base-tip collision fails, names the rival file and a next-free-ID suggestion"
    else echo "FAIL: base-tip collision message incomplete"; fail=1; fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Case (f): the PR's own file already sits on the base tip (same path) -> exit 0
# ════════════════════════════════════════════════════════════════════════════
seed_repo samepath 0300
land_on_base "0300-own.erg"     # identical path to the branch's own added file
if out=$(SELF_PR_NUMBER=99 STUB_PR_LIST='[]' run_check 2>&1); then
    echo "PASS: same-path base hit is not flagged (exit 0)"
else
    echo "FAIL: same-path base hit wrongly flagged as a collision"; echo "$out"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case (g): the PR renames a base ticket (same ID, new slug) -> exit 0
# ════════════════════════════════════════════════════════════════════════════
seed_repo rename                # branch adds no new ticket; it renames one
git -C "$REPO" mv tickets/0001-base.erg tickets/0001-renamed.erg
# Rewrite the body so git's similarity detection does NOT pair the two paths
# (the real-world trigger: a respec that renames the slug AND rewrites the
# body shows up as delete(old)+add(new), not R).
cat > "$REPO/tickets/0001-renamed.erg" <<'ERG'
%erg 0.1
Title: Base ticket, respecified beyond similarity recognition
Created: 2026-06-18
Author: test

--- log ---
2026-06-18T00:00Z test created
2026-06-18T01:00Z test note respecified: new slug, new body

--- body ---
## Context
Entirely rewritten so the rename is not detected as one: different sections,
different wording, different length. The ID is the only thing that survives.

## Exit criteria
- [ ] nothing in common with the original body
ERG
git -C "$REPO" add tickets/0001-renamed.erg
git -C "$REPO" commit -q -m "rename slug + respec body"
if out=$(SELF_PR_NUMBER=99 STUB_PR_LIST='[]' run_check 2>&1); then
    echo "PASS: same-ID rename is not flagged (exit 0)"
else
    echo "FAIL: rename wrongly flagged as a base-tip collision"; echo "$out"; fail=1
fi

if (( fail )); then exit 1; fi
echo "PASS: cross-PR ticket-ID collision gate — collisions fail with a named PR, distinct IDs pass, no-ticket PRs skip the forge call, fetch failures warn, base-tip claims are caught, renames pass"
