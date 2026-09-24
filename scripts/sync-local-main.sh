#!/usr/bin/env bash
# Sync the local default branch (main/master) to origin, safely, from any
# checkout or linked worktree of the repo.
#
# Usage: sync-local-main.sh [checkout-dir] [branch]
#   checkout-dir  any checkout/worktree of the repo (default: .)
#   branch        branch to sync (default: detected default branch) — for
#                 repos whose integration branch is not main/master (ticket 0277)
#
# Guarantees (see rules/git.md § Local main syncs eagerly):
# - only the named/default branch moves — never whatever branch happens to be
#   checked out where the script runs;
# - fast-forward only: a diverged local default branch is reported, not moved;
# - no working tree is discarded or stashed: when the default branch is
#   checked out somewhere with conflicting local state, it is left untouched
#   and reported. Local state that already converged with the incoming commits
#   (byte-identical files, append-only memory indexes) is absorbed without
#   losing a byte — see "Converged local state" below (ticket 0972).
#
# Always exits 0 (fit for hooks): staleness is reported on stdout, never
# escalated to a failure that would break a session start or a merge flow.
set -euo pipefail

cd "${1:-.}" 2>/dev/null || { echo "sync-local-main: no such directory '${1:-.}' — skipped"; exit 0; }

git rev-parse --git-common-dir >/dev/null 2>&1 || { echo "sync-local-main: not a git repo — skipped"; exit 0; }
git remote get-url origin >/dev/null 2>&1 || { echo "sync-local-main: no origin remote — nothing to sync"; exit 0; }

# Branch to sync: explicit second argument, else the default branch from
# origin/HEAD, falling back to main, then master.
default="${2:-}"
if [ -z "$default" ]; then
    default=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||') || true
fi
if [ -z "${default:-}" ]; then
    if git show-ref --verify --quiet refs/heads/main; then default=main
    elif git show-ref --verify --quiet refs/heads/master; then default=master
    else echo "sync-local-main: no origin/HEAD and no local main/master — skipped"; exit 0
    fi
fi
git show-ref --verify --quiet "refs/heads/$default" || { echo "sync-local-main: no local branch '$default' — skipped"; exit 0; }

git fetch --quiet origin "$default" || { echo "sync-local-main: fetch failed (offline?) — skipped"; exit 0; }

local_sha=$(git rev-parse "refs/heads/$default")
remote_sha=$(git rev-parse "refs/remotes/origin/$default")
if [ "$local_sha" = "$remote_sha" ]; then
    exit 0
fi

if ! git merge-base --is-ancestor "refs/heads/$default" "refs/remotes/origin/$default"; then
    echo "sync-local-main: local $default has diverged from origin/$default — left untouched"
    exit 0
fi

# Name the state that actually refused the fast-forward, instead of the old
# "dirty or busy checkout" catch-all (ticket 0851).
#
# git has already stated why it refused, so `$err` is established evidence and
# a local probe of the checkout is only an inference. Classify from `$err`
# first; a checkout can be dirty in ways that have nothing to do with the
# refusal, and an inference that outranks the evidence reports a non-cause
# (reroll 1: an unrelated tracked edit displaced a real path collision, sending
# the operator to back up a file that was never in the way). Three outcomes:
#   - untracked/incoming path collision: git's own refusal, reported with the
#     colliding paths. Untracked files do NOT block a fast-forward in general —
#     the sync is attempted regardless and succeeds when nothing collides — so
#     folding this case into "dirty" told the operator to clean a checkout that
#     did not need cleaning;
#   - tracked modifications: taken when git's refusal names local changes, or
#     when git said nothing at all and the checkout is in fact dirty. The local
#     probe is a last resort, never a tie-breaker: a checkout can be dirty in a
#     file the fast-forward never touches, so `tracked_dirty` alone establishes
#     nothing about why git refused (escalation 2: an index.lock refusal beside
#     an unrelated tracked edit was reported as "tracked modifications", sending
#     the operator to back up a file and hiding a message that named the real
#     cause outright);
#   - anything else (a concurrent session's index.lock, a hook, a permission
#     error): git's own first line, verbatim. Whenever git said something these
#     tests do not recognise, quoting it beats guessing — the whole defect was a
#     message that named a cause it had not established.
# The merge runs under LC_ALL=C so this classification reads git's English
# messages on a French desktop as well as in CI.
# Each cause carries its own remedy: the old single tail ("back up the dirty
# file") is wrong advice for a checkout that is merely busy.

# True only on exit 1 — dirty tracked files. `git diff --quiet` also exits >1
# when git itself failed (permission denied, corrupt index), which is evidence
# of nothing and must not be folded into "dirty" (rules/coding-bash.md).
tracked_dirty() {
    local rc=0
    git -C "$1" diff --quiet HEAD 2>/dev/null || rc=$?
    [ "$rc" -eq 1 ]
}

# The paths git listed under one named error header. git prints a block as a
# header line followed by indented paths and terminated by the next unindented
# line, so anchoring on the header and stopping at that line keeps two blocks
# apart. Harvesting every indented line in the blob instead merges them — which
# is how a tracked, modified file was announced as untracked and the operator
# told to move it aside, advice that would have discarded uncommitted work
# (escalation 3). git can and does emit both blocks in one refusal.
# Truncation is announced rather than silent: a list capped at three with no
# marker reads as the complete set.
block_paths() {
    printf '%s\n' "$2" | awk -v hdr="$1" '
        index($0, hdr)             { inblock = 1; next }
        inblock && /^[[:space:]]/  { sub(/^[[:space:]]+/, ""); n++
                                     if (n <= 3) list = list (n > 1 ? " " : "") $0
                                     next }
        inblock                    { inblock = 0 }
        END { if (n > 3) list = list " (+" n - 3 " more)"; printf "%s", list }'
}

# The checkout's own dirty paths. Used only where git named no files itself: an
# isolated session cannot run `git -C <primary> status` (the worktree path guard
# refuses reads too), so this line is the only diagnostic it gets, and "dirty"
# without a path is what sent one session inferring the set from a stale
# snapshot.
local_dirty_paths() {
    git -C "$1" diff --name-only HEAD 2>/dev/null | awk '
        { n++; if (n <= 3) list = list (n > 1 ? " " : "") $0 }
        END { if (n > 3) list = list " (+" n - 3 " more)"; printf "%s", list }'
}

refusal_cause() {
    local dir="$1" err="$2" tracked untracked out line
    tracked=$(block_paths "local changes to the following files would be overwritten" "$err")
    untracked=$(block_paths "untracked working tree file" "$err")
    out=""

    if [ -n "$tracked" ]; then
        out="tracked modifications in the checkout: $tracked — back them up, sync, re-apply (rules/git.md)"
    elif [[ "$err" == *"Please commit your changes or stash them"* ]] \
         || { [ -z "${err//[[:space:]]/}" ] && tracked_dirty "$dir"; }; then
        out="tracked modifications in the checkout: $(local_dirty_paths "$dir") — back them up, sync, re-apply (rules/git.md)"
    fi

    if [ -n "$untracked" ]; then
        # Both blocks can be live at once. Report both: naming only one leaves
        # the operator to hit the other on the retry, and picking which to hide
        # is the guess this whole function exists to stop making.
        [ -n "$out" ] && out="$out; and separately, "
        out="${out}untracked files collide with the incoming $default: $untracked — move them aside, then re-run"
    fi

    if [ -n "$out" ]; then
        printf '%s' "$out"
        return 0
    fi

    line=$(printf '%s\n' "$err" | grep -v '^[[:space:]]*$' | head -1)
    printf '%s' "git refused: ${line:-no message} — nothing to clean here, re-run once the checkout is free"
}

# Converged local state (ticket 0972). Memory is written uncommitted into the
# live checkout and reaches origin later through a PR, so a refused
# fast-forward is usually refused by bytes it is about to write anyway. Two
# shapes carry no information and are absorbed; every other refusal stands:
#   - identical: a colliding file (untracked, or tracked with an unstaged edit)
#     whose content is byte-identical to the incoming blob;
#   - union: a memory index (`memory/MEMORY.md`) whose local edit only ADDED
#     lines. It is reset for the fast-forward, then rewritten as the incoming
#     index plus the local additions it lacks, left uncommitted as before.
#     The local diff, not the whole local file, supplies the lines: re-adding
#     the local copy of a line upstream removed would undo a sweep. A local
#     deletion is a decision a union cannot make, so it refuses.
# Every file is backed up before it is touched, and any failed step (backup,
# reset, removal) abandons the whole reconcile and puts back what was touched
# so far. If the retried fast-forward still fails, everything is restored and
# the retry's refusal is reported: the checkout ends exactly as it was found.
# Restoring never aborts the script (the hook contract is exit 0); a restore
# that cannot complete keeps the backup directory and names it.
RECON=""
recon_keep=0
recon_ident=0
recon_union=0

cleanup_recon() {
    if [ -n "$RECON" ] && [ "$recon_keep" = 0 ]; then
        rm -rf "$RECON"
    fi
    return 0
}
trap cleanup_recon EXIT

# Lines the local edit added to <path> relative to HEAD, blank ones included;
# exit 1 when the edit also deleted a line.
added_lines_only() {
    git -C "$1" diff --no-color --no-ext-diff -U0 HEAD -- "$2" | awk '
        /^@@/        { body = 1; next }
        !body        { next }
        /^-/         { deleted = 1; next }
        /^\+/        { print substr($0, 2) }
        END          { exit deleted }'
}

# The incoming index, a newline if it lacks a final one, then the local
# additions it does not already carry (blank lines always kept).
build_union() {
    local incoming_file="$1" add_file="$2"
    cat "$incoming_file"
    if [ -s "$incoming_file" ] && [ "$(tail -c1 "$incoming_file" | wc -l)" -eq 0 ]; then
        echo
    fi
    awk 'FILENAME == ARGV[1] { if ($0 != "") seen[$0] = 1; next }
         $0 == "" || !($0 in seen)' "$incoming_file" "$add_file"
}

# Put back every file touched so far. Never fails the script.
restore_reconciled() {
    local dir="$1" n p
    [ -n "$RECON" ] && [ -f "$RECON/touched" ] || return 0
    while IFS=$'\t' read -r n p; do
        if ! cp -p "$RECON/$n" "$dir/$p"; then
            recon_keep=1
            echo "sync-local-main: could not restore $p — its backup is kept at $RECON/$n"
        fi
    done < "$RECON/touched"
    return 0
}

# Abandon a reconcile midway: restore, and report nothing absorbed.
abandon_reconcile() {
    restore_reconciled "$1"
    recon_ident=0
    recon_union=0
    rm -f "$RECON/union"
    return 1
}

reconcile_converged() {
    local dir="$1" p incoming local_blob tracked n=0
    RECON=$(mktemp -d) || { RECON=""; return 1; }
    : > "$RECON/touched" || return 1
    while IFS= read -r p; do
        [ -f "$dir/$p" ] && [ ! -L "$dir/$p" ] || continue
        incoming=$(git -C "$dir" rev-parse --verify --quiet "refs/remotes/origin/$default:$p") || continue
        if git -C "$dir" ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then
            tracked=1
            git -C "$dir" diff --cached --quiet HEAD -- "$p" || continue   # staged: not ours to touch
            ! git -C "$dir" diff --quiet -- "$p" || continue               # clean: not in the way
        else
            tracked=0
        fi
        local_blob=$(git -C "$dir" hash-object -- "$p") || continue
        n=$((n + 1))
        if [ "$local_blob" = "$incoming" ]; then
            { cp -p "$dir/$p" "$RECON/$n" &&
              printf '%s\t%s\n' "$n" "$p" >> "$RECON/touched" &&
              if [ "$tracked" = 1 ]; then
                  git -C "$dir" show "HEAD:$p" > "$dir/$p"
              else
                  rm -f "$dir/$p"
              fi
            } || { abandon_reconcile "$dir"; return 1; }
            recon_ident=$((recon_ident + 1))
        elif [ "$tracked" = 1 ] && [[ "/$p" == */memory/MEMORY.md ]] \
             && added_lines_only "$dir" "$p" > "$RECON/$n.add"; then
            { git -C "$dir" cat-file blob "$incoming" > "$RECON/$n.in" &&
              build_union "$RECON/$n.in" "$RECON/$n.add" > "$RECON/$n.union" &&
              cp -p "$dir/$p" "$RECON/$n" &&
              printf '%s\t%s\n' "$n" "$p" >> "$RECON/touched" &&
              printf '%s\t%s\n' "$n" "$p" >> "$RECON/union" &&
              git -C "$dir" show "HEAD:$p" > "$dir/$p"
            } || { abandon_reconcile "$dir"; return 1; }
            recon_union=$((recon_union + 1))
        fi
    done < <(git -C "$dir" diff --name-only --no-renames "$local_sha" "$remote_sha")
    [ $((recon_ident + recon_union)) -gt 0 ]
}

# After the fast-forward: rewrite each union. A failed write leaves the file at
# the incoming version, so the local additions stay in the backup, named.
apply_unions() {
    local dir="$1" n p
    [ -f "$RECON/union" ] || return 0
    while IFS=$'\t' read -r n p; do
        if ! cat "$RECON/$n.union" > "$dir/$p"; then
            recon_keep=1
            echo "sync-local-main: could not re-apply local additions to $p — kept at $RECON/$n"
        fi
    done < "$RECON/union"
    return 0
}

recon_note() {
    local parts=()
    [ "$recon_ident" -gt 0 ] && parts+=("$recon_ident path(s) already identical upstream")
    [ "$recon_union" -gt 0 ] && parts+=("$recon_union memory index(es) merged by union, local additions left uncommitted")
    local IFS=';'
    printf ' — absorbed %s' "${parts[*]}"
}

try_ff() {
    LC_ALL=C git -C "$1" merge --ff-only --quiet "origin/$default" 2>&1 >/dev/null
}

# Where (if anywhere) is the default branch checked out? Refs are shared
# across worktrees, so one sync covers them all.
#
# `git worktree list --porcelain` is a live output-rewrite target: a
# framing/summarising hook can inject banner lines into its stdout. Parse
# defensively so such lines cannot corrupt the checkout-location extraction:
#   - grep keeps only lines that begin with a porcelain record key, dropping
#     any injected banner (e.g. "--- Changes ---"); `|| true` keeps the empty
#     result from tripping pipefail;
#   - the awk requires exactly two fields on a `branch` record (NF == 2), so a
#     malformed, extra-field summary line ("branch refs/heads/main is stale")
#     cannot satisfy the ref match and double-emit a path.
# Porcelain paths may contain spaces, so the `worktree` line keeps substr and no
# arity check. (ticket 0333)
co_path=$(git worktree list --porcelain 2>/dev/null \
    | { grep -E '^(worktree |HEAD |branch |detached$|bare$|$)' || true; } \
    | awk -v ref="refs/heads/$default" \
        '$1 == "worktree" { path = substr($0, 10) } $1 == "branch" && NF == 2 && $2 == ref { print path }')

if [ -z "$co_path" ]; then
    # Not checked out anywhere: ff-update the ref from the remote-tracking
    # ref line 32 already fetched — fetching from "." costs no second network
    # round-trip, and fetch still refuses non-ff and checked-out targets, so
    # this can never clobber anything.
    if git fetch --quiet . "refs/remotes/origin/$default:refs/heads/$default"; then
        echo "sync-local-main: $default updated by ref $local_sha -> $remote_sha"
    else
        echo "sync-local-main: ref update of $default refused — left untouched"
    fi
elif ff_err=$(try_ff "$co_path"); then
    echo "sync-local-main: $default fast-forwarded at $co_path ($local_sha -> $remote_sha)"
elif reconcile_converged "$co_path" && ff_retry=$(try_ff "$co_path"); then
    apply_unions "$co_path"
    echo "sync-local-main: $default fast-forwarded at $co_path ($local_sha -> $remote_sha)$(recon_note)"
else
    # The retry's refusal names only the genuine blockers; the absorbed paths
    # would send the operator after files that were never in the way.
    [ -n "${ff_retry:-}" ] && ff_err=$ff_retry
    [ -n "$RECON" ] && restore_reconciled "$co_path"
    echo "sync-local-main: could not fast-forward $default at $co_path, left untouched — $(refusal_cause "$co_path" "$ff_err")"
fi
exit 0
