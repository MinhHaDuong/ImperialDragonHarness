#!/usr/bin/env bash
# Roar steps 7-10 in one command (ticket 1084): ticket close, close-claim
# check, tracker-sibling detection, worktree-exit preflight, branch sweep.
#
# The model used to retype these as bash blocks, one turn each, every turn
# re-reading the whole session context. The judgment stays in SKILL.md; this
# script only does what is deterministic and ends with a one-screen report.
#
# Exit codes — 0 clean, 1 findings, 2 could-not-look. 2 is never an all-clear:
# a missing ticket store, an unreadable forge or a failed fetch all land there.
#
# Phases exist because step 9 (ExitWorktree) sits between the preflight and
# the sweep, and the sweep's current-branch guard depends on the cwd:
#   before-exit  close, close claims, tracker detection, preflight
#   preflight    the worktree-exit preflight alone, run fresh right before
#                ExitWorktree (the before-exit result predates the wrap-up work)
#   after-exit   local and remote branch sweep
#   all          both (default; for a roar that is not in a worktree)
#
# Guard lines in the sweep carry a `# guard:<name>` tag so that
# tests/test_roar_close_and_clean.sh can strip exactly one and show the
# unguarded script destroys something or fails.
set -euo pipefail

TICKET=""
DAYS=7
DEFAULT=""
PHASE=all
while [ $# -gt 0 ]; do
    case "$1" in
        --ticket|--days|--default-branch|--phase)
            [ $# -ge 2 ] || { echo "close-and-clean: $1 needs a value" >&2; exit 2; } ;;&
    esac
    case "$1" in
        --ticket)         TICKET="$2"; shift 2 ;;
        --days)           DAYS="$2"; shift 2 ;;
        --default-branch) DEFAULT="$2"; shift 2 ;;
        --phase)          PHASE="$2"; shift 2 ;;
        -h|--help)
            echo "usage: close-and-clean.sh [--ticket NNNN] [--days N] [--default-branch B] [--phase before-exit|preflight|after-exit|all]"
            echo "  Roar steps 7-10. Exit 0 clean, 1 findings, 2 could-not-look."
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
    if [ "$(git rev-parse --git-dir)" = "$(git rev-parse --git-common-dir)" ]; then
        note "PREFLIGHT: skipped (not in a linked worktree)"
        return 0
    fi
    local rc=0
    "$IDH_ROOT/scripts/worktree-exit-preflight.sh" || rc=$?
    case "$rc" in
        0) note "PREFLIGHT: ok" ;;
        1) note "PREFLIGHT: DIRTY — commit or salvage, then re-run --phase before-exit"; bump 1 ;;
        *) note "PREFLIGHT: COULD-NOT-LOOK (exit $rc)"; bump 2 ;;
    esac
}

# ── Step 10: the branch sweep ─────────────────────────────────────────────────
# Delete only after the ancestry probe: a plain delete has no merged-check of
# its own, and a remote branch can be the only copy of a colleague's work.
# Every delete is isolated (`if probe; then delete || FAIL`): a refused delete
# is reported and the sweep carries on, instead of aborting under `set -e`
# with every later branch never swept.
# True when <ref> (a full refname) is merged into $base_tip and safe to delete. The
# ref is resolved ONCE, to PROBED, and the ancestry test runs on that object id: the
# delete is then leased to PROBED, so a ref that moves after the verdict (a push, a
# concurrent fetch) is refused, never destroyed. A branch whose tip IS the base tip
# carries no work of its own — it may be a colleague's branch created a moment ago —
# so it is kept. A probe that errors (not "not an ancestor") is a could-not-look,
# never read as "unmerged, all fine".
PROBED=""
probe() { # <full refname>
    local rc=0
    PROBED=$(git rev-parse --verify -q "$1^{commit}") || { note "SWEEP: COULD-NOT-LOOK cannot resolve $1"; bump 2; return 1; }
    [ "$PROBED" = "$base_tip" ] && return 1
    git merge-base --is-ancestor "$PROBED" "$base_tip" || rc=$?
    case "$rc" in
        0) return 0 ;;
        1) return 1 ;;
        *) note "SWEEP: COULD-NOT-LOOK ancestry probe failed for $1"; bump 2; return 1 ;;
    esac
}

# True when any worktree stands on <branch>. Asked again at delete time, not only
# once up front: a session may check the branch out meanwhile. Fails closed — a
# worktree list that cannot be read keeps the branch.
checked_out() { # <branch>
    local l
    l=$(git worktree list --porcelain) || { note "SWEEP: COULD-NOT-LOOK worktree list failed — keeping $1"; bump 2; return 0; }
    printf '%s\n' "$l" | awk '/^branch /{sub("refs/heads/","",$2); print $2}' | grep -qxF -- "$1"
}

# Put back a branch the sweep removed at a tip the probe never approved. Recreates only
# an absent ref (the empty old value), so it cannot overwrite a branch made meanwhile.
restore_branch() { # <branch> <abbreviated sha git reported>
    local full
    [ -n "$2" ] && full=$(git rev-parse --verify -q "$2^{commit}") &&
        git update-ref "refs/heads/$1" "$full" "" >/dev/null 2>&1
}

sweep() {
    local has_origin=0 b cur failed=0 deleted="" kept="" rdeleted="" rkept="" lbranches="" rbranches=""
    git remote get-url origin >/dev/null 2>&1 && has_origin=1
    # Full refnames throughout: an unqualified `origin/main` or `main` is shadowed by a
    # tag of that name, and the probe would then approve against the wrong commit.
    if [ "$has_origin" -eq 1 ]; then
        if ! git fetch --prune origin >/dev/null 2>&1; then
            note "SWEEP: COULD-NOT-LOOK git fetch --prune failed — nothing deleted, not an all-clear"
            bump 2; return 0
        fi
        if [ -z "$DEFAULT" ]; then
            DEFAULT=$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null || true)
            DEFAULT="${DEFAULT#refs/remotes/origin/}"
        fi
        DEFAULT="${DEFAULT:-main}"
        base="refs/remotes/origin/$DEFAULT"
    else
        # No-forge repo: "merged" means contained in the local default branch.
        DEFAULT="${DEFAULT:-main}"
        base="refs/heads/$DEFAULT"
    fi
    if ! base_tip=$(git rev-parse --verify -q "$base^{commit}"); then
        note "SWEEP: COULD-NOT-LOOK no $base to probe against"
        bump 2; return 0
    fi

    # Enumerate into variables, not process substitutions: a failed for-each-ref
    # inside `< <(...)` is invisible to set -e and reads as an empty, clean sweep.
    # lstrip, not :short — :short prints `heads/x` when a tag or remote ref shares the
    # name, and the whole-line guards below would then miss it.
    cur=$(git branch --show-current)
    lbranches=$(git for-each-ref --format='%(refname:lstrip=2)' refs/heads/) ||
        { note "SWEEP: COULD-NOT-LOOK cannot list local branches"; bump 2; lbranches=""; }
    while IFS= read -r b; do
        [ -n "$b" ] || continue
        [ "$b" = "$DEFAULT" ] && continue   # guard:default — always an ancestor of itself; with HEAD detached nothing else protects it
        [ "$b" = "$cur" ] && continue       # guard:current — never delete the branch you are standing on
        # guard:worktree — a branch checked out in ANY worktree is another session's; matched
        # on whole LINES (a space-delimited membership test silently never fires, 2026-09-10).
        checked_out "$b" && continue  # guard:worktree
        if probe "refs/heads/$b"; then
            # `git branch -D`, not `update-ref -d <oid>`: update-ref has the compare-and-set but
            # none of git's refusal to delete a branch a worktree stands on, and an occupancy
            # list read before the delete can never close that gap (a peer checks the branch
            # out in between). branch -D makes the refusal itself, inside the delete. It names
            # the tip it removed ("was <sha>"); one that is not the probed commit means the
            # branch moved after the probe, and is put back (nothing is lost: the object is
            # still there, and only an absent ref is recreated).
            if del=$(LC_ALL=C git branch -D -- "$b" 2>&1); then
                was=$(printf '%s\n' "$del" | sed -n 's/.*(was \([0-9a-f]\{7,\}\)).*/\1/p' | head -1)
                if [ -n "$was" ] && [[ "$PROBED" == "$was"* ]]; then
                    git config --remove-section "branch.$b" >/dev/null 2>&1 || true
                    deleted="$deleted $b"
                else
                    failed=$((failed + 1))
                    if restore_branch "$b" "$was"; then   # guard:restore
                        note "SWEEP: FAILED local $b moved since the probe — restored at $was"
                    else
                        note "SWEEP: FAILED local $b deleted at an unprobed tip (${was:-unknown}), not restorable"; bump 2
                    fi
                fi
            else
                failed=$((failed + 1)); note "SWEEP: FAILED to delete local $b (refused: ${del##*error: })"
            fi
        else
            kept="$kept $b"
        fi
    done <<<"$lbranches"

    if [ "$has_origin" -eq 1 ]; then
        rbranches=$(git for-each-ref --format='%(refname:lstrip=3)' refs/remotes/origin/) ||
            { note "SWEEP: COULD-NOT-LOOK cannot list remote branches"; bump 2; rbranches=""; }
        while IFS= read -r b; do
            [ -n "$b" ] || continue
            # origin/HEAD is a symref, listed as a branch named HEAD; deleting it fails
            # and, unisolated under `set -e`, aborted the whole sweep (2026-08-14).
            [ "$b" = HEAD ] && continue  # guard:symref
            [ "$b" = "$DEFAULT" ] && continue
            # The lease pins the delete to the commit the probe approved (PROBED, read once
            # inside probe): a push landing between the fetch and here is refused, not
            # destroyed. Full refname also sidesteps a tag of the same name.
            if probe "refs/remotes/origin/$b"; then
                if git push --force-with-lease="refs/heads/$b:$PROBED" origin ":refs/heads/$b" >/dev/null 2>&1; then rdeleted="$rdeleted $b"; else failed=$((failed + 1)); note "SWEEP: FAILED to delete remote $b"; fi
            else
                rkept="$rkept $b"
            fi
        done <<<"$rbranches"
    else
        note "SWEEP: no origin — remote side skipped; probes compare against local $DEFAULT"
    fi

    note "SWEEP: local deleted:${deleted:- none}; unmerged kept:${kept:- none}"
    [ "$has_origin" -eq 1 ] && note "SWEEP: remote deleted:${rdeleted:- none}; unmerged kept:${rkept:- none}"
    if [ "$failed" -gt 0 ]; then bump 1; fi
    return 0
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
    sweep ;;
esac

case "$SEV" in
    0) note "RESULT: clean" ;;
    1) note "RESULT: findings (exit 1)" ;;
    *) note "RESULT: could-not-look (exit 2) — not an all-clear" ;;
esac
exit "$SEV"
