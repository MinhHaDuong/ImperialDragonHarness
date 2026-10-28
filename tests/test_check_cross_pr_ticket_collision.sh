#!/usr/bin/env bash
# Regression suite for scripts/check-cross-pr-ticket-collision.sh.
#
# The optimistic-ID trap (git-erg#282) bites across open PRs: two branches can
# add the same ticket ID and every per-branch check passes. This script fails a
# PR whose added ticket ID is also added by another open PR.
#
# Method (from the retired merge-helper suite): a self-contained temp repo, a `gh`
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
#   (h) unreadable open-PR list fails closed (exit 2).
# Additional controls cover repository+branch self inference, no own open PR,
# genuine same-ID siblings, foreign same-name branches, ambiguous/missing
# source identity and explicit override bypass.
set -euo pipefail
# Hermetic children (ticket 0875): the checker is exercised as
# `bash "$SCRIPT"` against a stubbed gh, and such a child inherits BASH_ENV —
# re-running the project .env loader inside the very process whose collision
# verdicts are under test. Nothing here reads project .env values, so clear
# the loader suite-wide (rules/coding-bash.md).
export BASH_ENV=
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
    [[ -n "${STUB_PR_LIST_FAIL:-}" ]] && { echo "gh: not logged in" >&2; exit 4; }
    printf '%s\n' "$STUB_PR_LIST" ;;
  "api "*|"api")
    # Emulate `gh api ... --jq '...'`: forge.py asks for "filename<TAB>status" lines.
    [[ -n "${STUB_API_FAIL:-}" ]] && exit 1
    for f in ${STUB_SIBLING_FILES:-}; do printf '%s\tadded\n' "$f"; done ;;
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
      STUB_PR_LIST_FAIL="${STUB_PR_LIST_FAIL:-}" \
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
    else echo "FAIL: collision message incomplete"; echo "$out"; fail=1; fi
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
    else echo "FAIL: base-tip collision message incomplete"; echo "$out"; fail=1; fi
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

# ════════════════════════════════════════════════════════════════════════════
# Case (h): gh cannot list open PRs -> exit 2 (fail closed), one clear line
# ════════════════════════════════════════════════════════════════════════════
seed_repo ghdown 0300
rc=0
out=$(SELF_PR_NUMBER=99 STUB_PR_LIST_FAIL=1 run_check 2>&1) || rc=$?
if [[ "$rc" -eq 2 ]] && echo "$out" | grep -qF 'cross-pr-collision: cannot list open PRs (no gh auth/network/GitHub remote)'; then
    echo "PASS: gh failure fails closed (exit 2) with one clear line"
else
    echo "FAIL: gh failure should exit 2 with the clear line (got rc=$rc)"; echo "$out"; fail=1
fi

# Infer the open PR locally: never fetch its own files. Self is the origin's owner/name,
# read off its URL (ticket 1325); the seeded objects are already fetched.
seed_repo inferred 0300
git -C "$REPO" remote set-url origin "git@github-alias:me/repo.git"
GHLOG="$WORK/inferred.log"; : > "$GHLOG"
rc=0
out=$(STUB_GH_LOG="$GHLOG" \
      STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 0 ]] && ! grep -q 'api repos' "$GHLOG"; then
    echo "PASS: inferred self PR excluded without fetching its files"
else
    echo "FAIL: own inferred PR was scanned (rc=$rc)"; echo "$out"; fail=1
fi

# Inferred own PR is excluded while a genuine sibling collision fails.
rc=0
out=$(\
      STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}},{"number":77,"headRefName":"sibling"}]' \
      STUB_SIBLING_FILES='tickets/0300-sibling.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 1 ]] && grep -q '#77' <<< "$out" && ! grep -q '#99' <<< "$out"; then
    echo "PASS: inferred self excluded and genuine sibling collision fails"
else
    echo "FAIL: inferred self/sibling collision incorrect (rc=$rc)"; echo "$out"; fail=1
fi

# No own open PR: scan every sibling.
rc=0
out=$(STUB_PR_LIST='[{"number":77,"headRefName":"sibling"}]' \
      STUB_SIBLING_FILES='tickets/0300-sibling.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 1 ]] && grep -q '#77' <<< "$out"; then
    echo "PASS: branch without an open PR scans the full sibling list"
else
    echo "FAIL: branch without PR skipped sibling (rc=$rc)"; echo "$out"; fail=1
fi

# Ambiguous self claims are uncertainty, never a renumber recommendation.
rc=0
out=$(\
      STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}},{"number":88,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 2 ]] && ! grep -q 'Renumber your' <<< "$out"; then
    echo "PASS: ambiguous self fails closed without renumber advice"
else echo "FAIL: ambiguous self produced unsafe verdict (rc=$rc)"; echo "$out"; fail=1; fi

# A foreign fork's same-named branch is a sibling, never self.
rc=0
out=$(\
      STUB_PR_LIST='[{"number":55,"headRefName":"pr-inferred","isCrossRepository":true,"headRepository":{"nameWithOwner":"other/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-foreign.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 1 ]] && grep -q '#55' <<< "$out"; then
    echo "PASS: foreign fork with same branch name remains a collision"
else echo "FAIL: foreign same-name PR excluded (rc=$rc)"; echo "$out"; fail=1; fi

# Same-named own and foreign branches: exclude only the proven own source.
rc=0
out=$(\
      STUB_PR_LIST='[{"number":55,"headRefName":"pr-inferred","isCrossRepository":true,"headRepository":{"nameWithOwner":"other/repo"}},{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-foreign.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 1 ]] && grep -q '#55' <<< "$out" && ! grep -q '#99' <<< "$out"; then
    echo "PASS: same-name own source excluded while foreign sibling collides"
else echo "FAIL: same-name source verification incorrect (rc=$rc)"; echo "$out"; fail=1; fi

# Ticket 1325: from a fork checkout the PR's own head is cross-repository relative to the base,
# yet its head repository is the local origin: it is self, never a rival claim.
git -C "$REPO" remote set-url origin "https://github.com/me/fork.git"
rc=0
out=$(STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","isCrossRepository":true,"headRepository":{"nameWithOwner":"me/fork"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 0 ]] && ! grep -q '#99' <<< "$out"; then
    echo "PASS: fork checkout excludes its own cross-repository PR"
else echo "FAIL: fork checkout took its own PR for a rival (rc=$rc)"; echo "$out"; fail=1; fi

# GitHub owner/name are case-insensitive: an origin cloned in another case is still self.
git -C "$REPO" remote set-url origin "https://github.com/Me/Repo.git"
rc=0
out=$(STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 0 ]] && ! grep -q '#99' <<< "$out"; then
    echo "PASS: origin URL in another case still names self"
else echo "FAIL: origin case mismatch took own PR for a rival (rc=$rc)"; echo "$out"; fail=1; fi

# The local origin's identity unreadable: self cannot be established, fail closed.
git -C "$REPO" remote set-url origin "nonsense"
rc=0
out=$(STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
if [[ "$rc" == 2 ]] && ! grep -q 'Renumber your' <<< "$out"; then
    echo "PASS: unreadable origin identity fails closed without renumber advice"
else echo "FAIL: unreadable origin identity unsafe (rc=$rc)"; echo "$out"; fail=1; fi
git -C "$REPO" remote set-url origin "git@github-alias:me/repo.git"

# A detached HEAD cannot establish self: fail closed without renumber advice.
git -C "$REPO" switch -q --detach
rc=0
out=$(STUB_PR_LIST='[{"number":99,"headRefName":"pr-inferred","headRepository":{"nameWithOwner":"me/repo"}}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) || rc=$?
git -C "$REPO" switch -q "$BRANCH"
if [[ "$rc" == 2 ]] && ! grep -q 'Renumber your' <<< "$out"; then
    echo "PASS: unavailable self branch fails closed without renumber advice"
else echo "FAIL: unavailable self branch unsafe (rc=$rc)"; echo "$out"; fail=1; fi

# Explicit override bypasses branch inference: #99 is excluded though no branch matches.
out=$(SELF_PR_NUMBER=99 \
      STUB_PR_LIST='[{"number":99,"headRefName":"other-branch"}]' \
      STUB_SIBLING_FILES='tickets/0300-own.erg' run_check 2>&1) \
    && echo "PASS: explicit override bypasses inference" \
    || { echo "FAIL: override did not exclude its own PR"; echo "$out"; fail=1; }

# ════════════════════════════════════════════════════════════════════════════
# Ticket 1318: the none backend — no origin remote answers a typed skip, never a silent pass
# of an unread forge; origin remote with no gh fails closed.
# ════════════════════════════════════════════════════════════════════════════
NOGH="$WORK/nogh"; mkdir -p "$NOGH"
for tool in bash git jq python3 grep sed sort tr comm dirname cat env; do
    ln -sf "$(command -v "$tool")" "$NOGH/$tool"
done
run_nogh() { ( cd "$REPO"; PATH="$NOGH" BASE_REF="origin/$BASE" SELF_PR_NUMBER=99 bash "$SCRIPT" ); }

seed_repo nogh_origin 0300
rc=0; out=$(run_nogh 2>&1) || rc=$?
if [[ "$rc" == 2 ]] && grep -qF 'cannot list open PRs' <<< "$out"; then
    echo "PASS: origin remote without gh fails closed (exit 2)"
else echo "FAIL: origin without gh should exit 2 (rc=$rc)"; echo "$out"; fail=1; fi

git -C "$REPO" remote remove origin
git -C "$REPO" update-ref refs/remotes/origin/"$BASE" "$BASE"
rc=0; out=$(run_nogh 2>&1) || rc=$?
if [[ "$rc" == 0 ]] && grep -qF 'skipped: no forge' <<< "$out" && ! grep -q ' OK\.' <<< "$out"; then
    echo "PASS: no origin remote answers a typed 'skipped: no forge', not an all-clear"
else echo "FAIL: no forge should skip legibly (rc=$rc)"; echo "$out"; fail=1; fi

# Ticket 1325: no forge never discards a base-tip collision already counted.
seed_repo noforge_basecol 0300
land_on_base "0300-merged-sibling.erg"
git -C "$REPO" remote remove origin
git -C "$REPO" update-ref refs/remotes/origin/"$BASE" "$BASE"
rc=0; out=$(run_nogh 2>&1) || rc=$?
if [[ "$rc" == 1 ]] && grep -q '0300-merged-sibling' <<< "$out" && grep -q 'Renumber your' <<< "$out"; then
    echo "PASS: no forge still fails a base-tip collision (exit 1)"
else echo "FAIL: no forge discarded a base-tip collision (rc=$rc)"; echo "$out"; fail=1; fi

if (( fail )); then exit 1; fi
echo "PASS: cross-PR ticket-ID collision gate — collisions fail with a named PR, distinct IDs pass, no-ticket PRs skip the forge call, fetch failures warn, base-tip claims are caught, renames pass"
