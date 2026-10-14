#!/usr/bin/env bash
# Roar steps 7-10 in one command (ticket 1084): ticket close, close-claim
# check, tracker-sibling detection, worktree-exit preflight, scoped branch cleanup.
#
# The model used to retype these as bash blocks, one turn each, every turn
# re-reading the whole session context. The judgment stays in SKILL.md; this
# script only does what is deterministic and ends with a one-screen report.
#
# Exit codes — 0 clean, 1 findings, 2 could-not-look. 2 is never an all-clear:
# an unreadable existing ticket store, forge or Git metadata yields 2. A repo
# without tickets/ explicitly skips that workflow and may still exit cleanly.
#
# Phases exist because step 9 (worktree removal) sits between the preflight and
# the cleanup, and the cleanup's current-branch guard depends on the cwd:
#   before-exit  close, close claims, tracker detection, preflight
#   preflight    the worktree-exit preflight alone, run fresh right before
#                the removal (the before-exit result predates the wrap-up work)
#   after-exit   local and remote scoped branch cleanup
#   all          both (default; for a roar that is not in a worktree)
#
set -euo pipefail

TICKET=""
DAYS=7
DEFAULT=""
PHASE=all
LOCAL_TARGETS=()
REMOTE_TARGETS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --ticket|--days|--default-branch|--phase|--local-branch|--remote-branch)
            [ $# -ge 2 ] || { echo "close-and-clean: $1 needs a value" >&2; exit 2; } ;;&
    esac
    case "$1" in
        --local-branch)   LOCAL_TARGETS+=("$2"); shift 2 ;;
        --remote-branch)  REMOTE_TARGETS+=("$2"); shift 2 ;;
        --ticket)         TICKET="$2"; shift 2 ;;
        --days)           DAYS="$2"; shift 2 ;;
        --default-branch) DEFAULT="$2"; shift 2 ;;
        --phase)          PHASE="$2"; shift 2 ;;
        -h|--help)
            echo "usage: close-and-clean.sh [--ticket NNNN] [--days N] [--default-branch B] [--phase before-exit|preflight|after-exit|all] [--local-branch B=OID] [--remote-branch B=OID]"
            echo "  Roar steps 7-10. Exit 0 clean, 1 findings, 2 could-not-look."
            echo "  Repeat branch options only for this completed task; OID is its merged PR head (full hex)."
            exit 0 ;;
        *) echo "close-and-clean: unknown argument '$1'" >&2; exit 2 ;;
    esac
done
case "$PHASE" in before-exit|preflight|after-exit|all) ;; *) echo "close-and-clean: bad --phase '$PHASE'" >&2; exit 2 ;; esac

ROAR_DIR="${CLOSE_AND_CLEAN_ROAR_DIR:-$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
IDH_ROOT="${IDH_ROOT:-$(cd -P "$ROAR_DIR/../.." && pwd -P)}"

SEV=0
base=""; base_tip=""
note() { echo "roar: $*"; }
bump() { [ "$1" -gt "$SEV" ] && SEV=$1; return 0; }

ticket_file() { # <id> → path of the ticket, open or archived
    local f
    for f in tickets/"$1"-*.erg tickets/closed/"$1"-*.erg; do
        [ -f "$f" ] && { echo "$f"; return 0; }
    done
    return 1
}
is_closed() { grep -q '^Closed:' "$1"; }

# ── Step 7: close the ticket ──────────────────────────────────────────────────
close_ticket() {
    [ -n "$TICKET" ] || { note "CLOSE: skipped (no --ticket)"; return 0; }
    if [ ! -d tickets ]; then
        # No ticket workflow in this repo: the SKILL.md prerequisite policy, an explicit skip.
        note "CLOSE: skipped (no tickets/ directory — this repo has no ticket store)"
        return 0
    fi
    if [ ! -x tickets/erg ]; then
        # A ticket store that cannot answer is not a repo without one.
        note "CLOSE: COULD-NOT-LOOK tickets/ exists but tickets/erg does not run — not an all-clear"
        bump 2; return 0
    fi
    local f
    f=$(ticket_file "$TICKET") || { note "CLOSE: COULD-NOT-LOOK no ticket $TICKET in tickets/"; bump 2; return 0; }
    if is_closed "$f"; then
        note "CLOSE: ALREADY-CLOSED $TICKET"   # the usual case after /merge
        return 0
    fi
    # Some erg versions archive on close; archive only what is still in place.
    if tickets/erg close "$TICKET" "closed at roar" >/dev/null &&
        { [ ! -f "$f" ] || tickets/erg archive "$TICKET" >/dev/null; }; then
        note "CLOSE: CLOSED-UNCOMMITTED $TICKET — commit the ticket move in the wrap-up bundle"
        bump 1
    else
        note "CLOSE: COULD-NOT-LOOK erg close/archive failed for $TICKET"
        bump 2
    fi
}

# ── Step 7: close claims of recently merged PRs ───────────────────────────────
check_claims() {
    local rc=0
    if [ ! -d tickets ]; then
        note "CLAIMS: skipped (no tickets/ directory — this repo has no ticket store)"
        return 0
    fi
    if [ ! -x tickets/erg ]; then
        note "CLAIMS: COULD-NOT-LOOK tickets/ exists but tickets/erg does not run — not an all-clear"
        bump 2; return 0
    fi
    # Not `|| true`: the exit code is the finding. DROPPED is reported, never
    # repaired here — commit and archive stay with the model.
    "$ROAR_DIR/check-close-claims.sh" --days "$DAYS" || rc=$?
    case "$rc" in
        0) note "CLAIMS: ok" ;;
        1) note "CLAIMS: FINDINGS (DROPPED/UNRESOLVED above)"; bump 1 ;;
        *) note "CLAIMS: COULD-NOT-LOOK (exit $rc) — not an all-clear"; bump 2 ;;
    esac
}

# ── Step 8: tracker-sibling detection (advisory; performing it is the model's) ─
detect_tracker() {
    [ -n "$TICKET" ] || return 0
    local f parent s open=0
    f=$(ticket_file "$TICKET") || return 0
    parent=$(sed -n 's/^Parent:[[:space:]]*\(tickets\/\)\{0,1\}\([0-9]\{4\}\).*/\2/p' "$f" | head -1)
    [ -n "$parent" ] || return 0
    for s in tickets/*.erg; do
        [ -f "$s" ] || continue
        grep -q "^Parent:[[:space:]]*\(tickets/\)\{0,1\}$parent" "$s" || continue
        is_closed "$s" || open=$((open + 1))
    done
    if [ "$open" -eq 0 ]; then
        note "TRACKER: INTEGRATION-REVIEW-DUE $parent"
    else
        note "TRACKER: parent $parent has $open open sibling(s); tracker stays open"
    fi
}

# ── Step 9a: worktree-exit preflight ──────────────────────────────────────────
preflight() {
    local git_dir common_dir rc=0
    if ! git_dir=$(git rev-parse --git-dir) ||
        ! common_dir=$(git rev-parse --git-common-dir) ||
        [ -z "$git_dir" ] || [ -z "$common_dir" ]; then
        note "PREFLIGHT: COULD-NOT-LOOK cannot read Git metadata paths"
        bump 2; return 0
    fi
    if [ "$git_dir" = "$common_dir" ]; then
        note "PREFLIGHT: skipped (not in a linked worktree)"
        return 0
    fi
    "$IDH_ROOT/scripts/worktree-exit-preflight.sh" || rc=$?
    case "$rc" in
        0) note "PREFLIGHT: ok" ;;
        1) note "PREFLIGHT: DIRTY — commit or salvage, then re-run --phase before-exit"; bump 1 ;;
        *) note "PREFLIGHT: COULD-NOT-LOOK (exit $rc)"; bump 2 ;;
    esac
}

# ── Step 10: explicitly scoped cleanup ───────────────────────────────────────
# The caller supplies only this completed task's PR source branches, pinned to
# their full reviewed/merged head OIDs. No refs are enumerated as candidates.
# Worktree ownership and exit remain the caller's responsibility.
validate_target() {
    local name="${1%%=*}" oid="${1#*=}"
    if [ "$name" = "$1" ] || ! git check-ref-format "refs/heads/$name" >/dev/null 2>&1 ||
        ! [[ "$oid" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]]; then
        note "SWEEP: COULD-NOT-LOOK invalid target '$1' (need branch=full-oid)"
        bump 2; return 1
    fi
}

# Exact refnames avoid tag shadowing. Check the supplied OID, never replace it
# with a newly read tip. Non-commit refs and symrefs cannot authorize deletion.
unchanged() { # <full refname> <expected oid>
    local actual rc=0
    git show-ref --verify --quiet "$1" >/dev/null 2>&1 || rc=$?
    case "$rc" in
        0) ;;
        1) note "SWEEP: ALREADY-ABSENT $1"; return 1 ;;
        *) note "SWEEP: COULD-NOT-LOOK cannot inspect $1"; bump 2; return 1 ;;
    esac
    rc=0
    git symbolic-ref -q "$1" >/dev/null 2>&1 || rc=$?
    case "$rc" in
        0) note "SWEEP: REFUSED symbolic target $1"; bump 1; return 1 ;;
        1) ;;
        *) note "SWEEP: COULD-NOT-LOOK cannot inspect symbolic target $1"; bump 2; return 1 ;;
    esac
    actual=$(git rev-parse --verify -q "$1") || {
        note "SWEEP: COULD-NOT-LOOK cannot resolve $1"; bump 2; return 1;
    }
    if [ "$actual" != "$2" ]; then
        note "SWEEP: DRIFT $1 — keeping changed tip"; bump 1; return 1
    fi
    git cat-file -e "$2^{commit}" 2>/dev/null || {
        note "SWEEP: COULD-NOT-LOOK target is not a commit: $1"; bump 2; return 1;
    }
}

remote_unchanged() { # <branch> <approved oid>; inspect the exact remote ref
    local answer rc=0
    answer=$(git ls-remote --exit-code --heads origin "refs/heads/$1") || rc=$?
    case "$rc" in
        0) ;;
        2) note "SWEEP: ALREADY-ABSENT remote refs/heads/$1"; return 1 ;;
        *) note "SWEEP: COULD-NOT-LOOK cannot inspect remote $1"; bump 2; return 1 ;;
    esac
    if [ "$answer" != "$(printf '%s\t%s' "$2" "refs/heads/$1")" ]; then
        note "SWEEP: DRIFT remote refs/heads/$1 — keeping changed tip"; bump 1; return 1
    fi
}

checked_out() { # <branch>; unreadable list refuses cleanup
    local listing
    listing=$(git worktree list --porcelain) || {
        note "SWEEP: COULD-NOT-LOOK worktree list failed — keeping $1"; bump 2; return 0;
    }
    if printf '%s\n' "$listing" | grep -qxF -- "branch refs/heads/$1"; then
        note "SWEEP: RETAINED $1 (occupied worktree)"; bump 1; return 0
    fi
    return 1
}

cleanup() {
    local has_origin=0 target b oid ref cur rc deleted="" rdeleted=""
    if [ "${#LOCAL_TARGETS[@]}" -eq 0 ] && [ "${#REMOTE_TARGETS[@]}" -eq 0 ]; then
        note "SWEEP: skipped (no explicit completed-task branch targets)"; return 0
    fi
    # Validate the entire requested scope before any mutation.
    for target in "${LOCAL_TARGETS[@]}" "${REMOTE_TARGETS[@]}"; do
        validate_target "$target" || return 0
    done
    git remote get-url origin >/dev/null 2>&1 && has_origin=1
    if [ "$has_origin" -eq 1 ]; then
        if [ -z "$DEFAULT" ]; then
            DEFAULT=$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null || true)
            DEFAULT="${DEFAULT#refs/remotes/origin/}"
        fi
        DEFAULT="${DEFAULT:-main}"
        base="refs/remotes/origin/$DEFAULT"
        if ! git check-ref-format "refs/heads/$DEFAULT" >/dev/null 2>&1 ||
            ! git check-ref-format "$base" >/dev/null 2>&1; then
            note "SWEEP: COULD-NOT-LOOK invalid default integration ref"; bump 2; return 0
        fi
        rc=0
        git symbolic-ref -q "$base" >/dev/null 2>&1 || rc=$?
        case "$rc" in
            1) ;;
            *) note "SWEEP: COULD-NOT-LOOK integration tracking ref is symbolic or unreadable"; bump 2; return 0 ;;
        esac
        # Ignore configured refspecs/opportunistic mappings: they can force-move
        # unrelated local heads. Fetch only the integration ref, with no tags,
        # pruning, submodule recursion or automatic repository maintenance.
        if ! git fetch --refmap= --no-prune --no-prune-tags --no-tags \
            --no-recurse-submodules --no-auto-gc --no-write-commit-graph origin \
            "+refs/heads/$DEFAULT:$base" >/dev/null 2>&1; then
            note "SWEEP: COULD-NOT-LOOK integration fetch failed — nothing deleted"; bump 2; return 0
        fi
    else
        DEFAULT="${DEFAULT:-main}"
        base="refs/heads/$DEFAULT"
        if [ "${#REMOTE_TARGETS[@]}" -gt 0 ]; then
            note "SWEEP: COULD-NOT-LOOK remote targets supplied without origin"; bump 2; return 0
        fi
    fi
    if ! base_tip=$(git rev-parse --verify -q "$base^{commit}") ||
        ! cur=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || { rc=$?; [ "$rc" -eq 1 ]; }); then
        note "SWEEP: COULD-NOT-LOOK cannot read integration base or current branch"; bump 2; return 0
    fi
    # An unreadable occupancy snapshot refuses the entire requested cleanup.
    if ! git worktree list --porcelain >/dev/null; then
        note "SWEEP: COULD-NOT-LOOK cannot read worktrees"; bump 2; return 0
    fi
    # Inspect the requested refs before any delete. Absence/drift is reported;
    # an unreadable prerequisite fails the whole initial cleanup closed.
    for target in "${LOCAL_TARGETS[@]}"; do
        unchanged "refs/heads/${target%%=*}" "${target#*=}" || true
    done
    for target in "${REMOTE_TARGETS[@]}"; do
        remote_unchanged "${target%%=*}" "${target#*=}" || true
    done
    [ "$SEV" -ge 2 ] && return 0
    cleanup_side local "${LOCAL_TARGETS[@]}"
    cleanup_side remote "${REMOTE_TARGETS[@]}"
    note "SWEEP: local deleted:${deleted:- none}; remote deleted:${rdeleted:- none}"
}

cleanup_side() { # <local|remote> <explicit targets...>
    local side="$1" head_check_remote; shift
    for target in "$@"; do
        b="${target%%=*}"; oid="${target#*=}"
        if [ "$b" = "$DEFAULT" ]; then
            note "SWEEP: RETAINED $side $b (default branch)"; bump 1; continue
        fi
        if [ "$b" = "$cur" ]; then
            note "SWEEP: RETAINED $side $b (current branch)"; bump 1; continue
        fi
        if [ "$b" = HEAD ]; then
            note "SWEEP: RETAINED $side $b (HEAD)"; bump 1; continue
        fi
        checked_out "$b" && continue
        if [ "$side" = local ]; then ref="refs/heads/$b"; else ref="refs/remotes/origin/$b"; fi
        if [ "$side" = local ]; then
            unchanged "$ref" "$oid" || continue
        else
            remote_unchanged "$b" "$oid" || continue
        fi
        rc=0
        git merge-base --is-ancestor "$oid" "$base_tip" || rc=$?
        case "$rc" in
            0) ;;
            1) note "SWEEP: UNMERGED $ref — kept"; bump 1; continue ;;
            *) note "SWEEP: COULD-NOT-LOOK ancestry failed for $ref"; bump 2; continue ;;
        esac
        if [ "$side" = local ]; then
            unchanged "$ref" "$oid" || continue
        else
            remote_unchanged "$b" "$oid" || continue
        fi
        checked_out "$b" && continue
        if [ "$side" = local ]; then
            # Keep Git's worktree and merge refusal. The target may normally
            # track itself on origin, so disable its upstream for this command
            # and use Git's conservative HEAD merge check. Config is unchanged.
            # The OID precheck is not atomic with branch -d: ordinary Git
            # semantics remain a backstop, not a universal concurrency promise.
            # A nonempty unconfigured remote avoids the empty-remote crash in
            # Git 2.53 for branches with an upstream. Inspect every alias key,
            # not merely a URL; never print config values (they may be private).
            head_check_remote="idh-roar-head-check-$oid"
            rc=0
            git config --get-regexp "^remote\.$head_check_remote\." >/dev/null 2>&1 || rc=$?
            case "$rc" in
                1) ;;
                0) note "SWEEP: RETAINED local $b (HEAD-check alias configured)"; bump 1; continue ;;
                *) note "SWEEP: COULD-NOT-LOOK cannot inspect HEAD-check alias for $b"; bump 2; continue ;;
            esac
            rc=0
            git -c "branch.$b.remote=$head_check_remote" branch -d -- "$b" >/dev/null 2>&1 || rc=$?
            case "$rc" in
                0) deleted="$deleted $b" ;;
                1) note "SWEEP: FAILED local $b — Git refused deletion; kept"; bump 1 ;;
                *) note "SWEEP: COULD-NOT-LOOK native deletion failed for $b (exit $rc)"; bump 2 ;;
            esac
        else
            if git push --force-with-lease="refs/heads/$b:$oid" origin ":refs/heads/$b" >/dev/null 2>&1; then
                rdeleted="$rdeleted $b"
            else
                note "SWEEP: FAILED remote $b — leased deletion refused"; bump 1
            fi
        fi
    done
}

case "$PHASE" in before-exit|all)
    close_ticket
    check_claims
    detect_tracker ;;
esac
case "$PHASE" in before-exit|preflight|all)
    preflight ;;
esac
case "$PHASE" in after-exit|all)
    cleanup ;;
esac

case "$SEV" in
    0) note "RESULT: clean" ;;
    1) note "RESULT: findings (exit 1)" ;;
    *) note "RESULT: could-not-look (exit 2) — not an all-clear" ;;
esac
exit "$SEV"
