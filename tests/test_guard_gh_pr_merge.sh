#!/usr/bin/env bash
# Tests for scripts/guard-gh-pr-merge.sh (tickets 0308, 0903).
#
# The guard has two jobs and they are tested apart, because they fire on
# different conditions and a test that conflates them cannot say which one
# spoke:
#
#   ADVISORY — any `gh pr merge` in a repo carrying a `tickets/` directory gets
#   a note on stdout saying the close claim is executed by `erg-pr-merge`, not
#   by the forge. Exit 0: the command still runs.
#
#   BLOCK — `--delete-branch` in a linked worktree only. Exit 2. The wider
#   block this file used to assert (any `gh pr merge` in any linked worktree)
#   was refuted on 2026-09-08 and case 4 below is that refutation, kept as a
#   standing test so the over-broad rule cannot come back.
#
# Note on the harness, learned the hard way while writing it: the runner sets
# `_out` and `_rc` as globals and is called as a plain command. A `rc=$(_run …)`
# form runs the function in a subshell, so its `_out` never reaches the caller
# and every stdout assertion fails while the guard is working perfectly. A test
# blind in that direction reports the same red as a real defect.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-gh-pr-merge.sh"
fail=0
_out=""
_rc=0

_payload() { # <command> → a PreToolUse payload carrying that command
    python3 -c 'import json,sys; print(json.dumps({"tool_input": {"command": sys.argv[1]}}))' "$1"
}

_run() { # <dir> [payload] → runs the hook from <dir>, sets _out and _rc
    local dir="$1" payload="${2:-{\}}"
    _rc=0
    _out=$( cd "$dir" && printf '%s' "$payload" | bash "$HOOK" 2>/dev/null ) || _rc=$?
}

_check() { # <label> <expected-rc>
    if [ "$2" = "$_rc" ]; then
        echo "PASS: $1"
    else
        echo "FAIL: $1 — expected rc $2, got $_rc"
        fail=1
    fi
}

_check_says() { # <label> <substring>
    case "$_out" in
        *"$2"*) echo "PASS: $1" ;;
        *) echo "FAIL: $1 — stdout did not carry '$2'"; fail=1 ;;
    esac
}

_check_silent() { # <label>
    if [ -z "$_out" ]; then
        echo "PASS: $1"
    else
        echo "FAIL: $1 — expected no stdout, got: $_out"
        fail=1
    fi
}

# Fixture A: a repo WITH a ticket store, plus a linked worktree and an ad-hoc one.
erg=$(mktemp -d)
git -C "$erg" init -q
mkdir -p "$erg/tickets"
touch "$erg/tickets/.keep"
git -C "$erg" -c user.email=t@t -c user.name=t add -A
git -C "$erg" -c user.email=t@t -c user.name=t commit -q -m init
mkdir -p "$erg/.claude/worktrees"
git -C "$erg" worktree add -q "$erg/.claude/worktrees/t001"
git -C "$erg" worktree add -q "$erg/adhoc"

# Fixture B: a repo with NO ticket store.
plain=$(mktemp -d)
git -C "$plain" init -q
git -C "$plain" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init

# --- The advisory ---------------------------------------------------------

# 1. A plain merge in a ticket repo → allowed, with the note.
_run "$erg" "$(_payload 'gh pr merge 449 --merge')"
_check "plain gh pr merge in a ticket repo is allowed" 0
_check_says "…and carries the close-claim note" "erg-pr-merge"

# 2. The note names the sanctioned command, so a reader has somewhere to go.
_check_says "…naming /merge" "/merge"

# 3. A repo with no ticket store → allowed and SILENT. This is the guard
#    minding its own business; without it the note would fire in every repo on
#    the machine. It is also the control for case 1: the two differ by the
#    presence of `tickets/` and nothing else, so a guard that always spoke and
#    a guard that reads the repo would disagree here.
_run "$plain" "$(_payload 'gh pr merge 12 --merge')"
_check "merge in a repo with no ticket store is allowed" 0
_check_silent "…and says nothing"

# 4. THE REFUTATION, kept as a standing test. `gh pr merge --merge` in a linked
#    worktree must NOT be blocked: it is a pure API call touching no local git,
#    and erg-pr-merge ran it from worktrees for PRs 808-826 without a failure
#    (2026-09-08). Before ticket 0903 this case exited 2.
_run "$erg/.claude/worktrees/t001" "$(_payload 'gh pr merge 449 --merge')"
_check "gh pr merge --merge in a worktree is NOT blocked" 0
_check_says "…and gets the advisory instead" "close claim"

# --- The narrow block -----------------------------------------------------

# 5. `--delete-branch` in a linked worktree → blocked. This is the part of the
#    old rule the refutation did not reach: the delete goes through the local
#    checkout and hits the parent's ref lock.
_run "$erg/.claude/worktrees/t001" "$(_payload 'gh pr merge 449 --merge --delete-branch')"
_check "gh pr merge --delete-branch in a worktree is blocked" 2

# 6. Same flag in an ad-hoc worktree outside .claude/worktrees/ → blocked too.
#    The ref lock does not care how the worktree was created (ticket 0308).
_run "$erg/adhoc" "$(_payload 'gh pr merge 449 -d')"
_check "short -d in an ad-hoc worktree is blocked" 2

# 7. `--delete-branch` in the PRIMARY checkout → allowed. No parent holds the
#    ref there.
_run "$erg" "$(_payload 'gh pr merge 449 --delete-branch')"
_check "--delete-branch in the primary checkout is allowed" 0

# --- Minding its own business --------------------------------------------

# 8. Ordinary work reaches this guard, because the `if:` matcher hands over any
#    command it cannot decompose. It must pass untouched and in silence
#    (2026-09-08: `erg log` was refused with a message about `gh pr merge`).
_run "$erg/.claude/worktrees/t001" "$(_payload 'erg log 0029 "$(cat note.txt)" tickets/')"
_check "an unrelated command in a worktree is allowed" 0
_check_silent "…and silently"

# 9. `git merge` is not the hazard: it is the documented recovery when
#    force-push is denied.
_run "$erg/.claude/worktrees/t001" "$(_payload 'git merge origin/main')"
_check "git merge is allowed" 0
_check_silent "…and silently"

# 10. Outside any git repo → allowed, silent. No repo, no ticket store, no
#     worktree predicate to evaluate.
tmp=$(mktemp -d)
_run "$tmp"
_check "outside any git repo is allowed" 0
_check_silent "…and silently"
rm -rf "$tmp"

# 11. A submodule is not a linked worktree — its git-dir equals its own
#     git-common-dir, so it shares no ref-lock with the superproject.
super=$(mktemp -d)
sub=$(mktemp -d)
git -C "$sub" init -q
git -C "$sub" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init-sub
git -C "$super" init -q
git -C "$super" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init-super
git -C "$super" -c protocol.file.allow=always -c user.email=t@t -c user.name=t \
    submodule add -q "$sub" mod 2>/dev/null
_run "$super/mod" "$(_payload 'gh pr merge 1 --delete-branch')"
_check "a submodule is not treated as a linked worktree" 0
rm -rf "$super" "$sub"

git -C "$erg" worktree remove --force "$erg/.claude/worktrees/t001" 2>/dev/null || true
git -C "$erg" worktree remove --force "$erg/adhoc" 2>/dev/null || true
rm -rf "$erg" "$plain"

exit $fail
