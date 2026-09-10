#!/bin/bash
set -euo pipefail
# Guard the `gh pr merge` command (ticket 0903). Two jobs, deliberately unequal.
#
# 1. ADVISORY (the reason this guard now exists). A PR body's
#    `**Ticket:** tickets/NNNN-...` line is executed by `erg-pr-merge`, not by
#    the forge. A bare `gh pr merge` bypasses it and the close claim is dropped
#    with no output — `erg check` passes either way, so the dropped close and a
#    clean merge produce identical evidence (git-erg PR #334, 2026-09-10: the
#    fix for ticket 0276 sat on main while 0276 stayed open). Emit a note, let
#    the command run.
#
# 2. BLOCK, narrowly. This file used to refuse `gh pr merge` in ANY linked
#    worktree, asserting git aborts there with `fatal: 'main' is already used by
#    worktree`. That premise was refuted on 2026-09-08: `erg-pr-merge` calls
#    `gh pr merge` from worktrees and did so for PRs 808 through 826 without a
#    single such failure. What the refutation does NOT reach is
#    `--delete-branch`, which checks out and deletes locally and can genuinely
#    fail against the parent checkout's ref lock. Narrow to that flag rather
#    than delete the true part with the false part.
#
# The old block message recommended `gh api .../merge -X PUT`, which is exactly
# the bypass job 1 exists to catch: the guard was steering toward the defect.
#
# WHY NO PR-BODY LOOKUP. Asking the forge whether *this* PR carries a close
# claim would need a network call inside a PreToolUse hook running under a 5 s
# timeout. A timed-out lookup yields an all-clear indistinguishable from "I
# could not look", which is not a check. The local `tickets/` directory answers
# the only question that matters here — does this repo have a close-claim
# machinery at all — with no network and no failure mode.
#
# WHY THE SANCTIONED PATH NEVER TRIPS THIS. `erg-pr-merge` is a script, so the
# matcher and this guard see `erg-pr-merge …` and never the string
# `gh pr merge` coming out of it. The only reachable trigger is a hand-typed
# merge, which is precisely the defect class.

payload=$(cat)
command=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    doc = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if isinstance(doc, dict):
    ti = doc.get("tool_input")
    if isinstance(ti, dict) and isinstance(ti.get("command"), str):
        print(ti["command"])
' 2>/dev/null) || command=""

# A command that was read and carries no gh-pr-merge shape is none of this
# guard's business. The glob stays loose (flags and `-R owner/repo` sit between
# the words). The `if:` matcher in settings.json hands over any command it
# cannot decompose — a command substitution, a heredoc, a loop — so ordinary
# work reaches here and must pass untouched (2026-09-08: `erg log` was refused
# with a message about `gh pr merge`).
if [ -n "$payload" ] && [ -n "$command" ]; then
    case "$command" in
        *gh*pr*merge*) ;;
        *) exit 0 ;;
    esac
fi

# Linked-worktree predicate (ticket 0308). A linked worktree's git-dir sits at
# `.../worktrees/<name>` under the common dir, so the two DIFFER; in the primary
# checkout and in a submodule (whose `.git` gitdir: file points at the
# superproject but whose ref-store is its own) they are EQUAL.
in_worktree() {
  local git_dir common_dir
  git_dir=$(git rev-parse --absolute-git-dir 2>/dev/null) || return 1
  common_dir=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ -n "$git_dir" ] || return 1
  [ -n "$common_dir" ] || return 1
  [ "$git_dir" != "$common_dir" ]
}

# Does this repo carry a ticket store, i.e. is there a close-claim machinery to
# bypass at all? Answered from the worktree root, which is where `tickets/`
# lives in a linked worktree too.
has_ticket_store() {
  local root
  root=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
  [ -n "$root" ] && [ -d "$root/tickets" ]
}

# Job 2, first: the narrow block. An unreadable command does NOT fail closed
# here. Fail-closed on an unreadable command is what refused real work on
# 2026-09-08, and the hazard is mild in the other direction: the merge itself
# is a pure API call that has already succeeded, and only the local branch
# delete fails — loudly, with git's own fatal.
case " ${command} " in
    *" --delete-branch"*|*" -d "*) delete_branch=1 ;;
    *) delete_branch=0 ;;
esac

if [ "$delete_branch" = 1 ] && in_worktree; then
  cat >&2 <<'EOF'
Blocked: `gh pr merge --delete-branch` deletes the branch through the local
checkout, which fails against the parent checkout's ref lock in a linked
worktree. The merge itself is fine from here — it is the branch delete that is
not.

Two ways on: drop the flag and delete the branch afterwards from the primary
checkout, or use `/merge`, which handles the merge and the cleanup together and
also honours the PR body's `**Ticket:**` close claim.
EOF
  exit 2
fi

# Job 1: the advisory. Runs whenever this repo has a ticket store, including
# for a command that could not be read — emitting a note costs nothing, and the
# note is what makes a silent failure visible.
if has_ticket_store; then
  cat <<'EOF'
Note on this merge: a PR body's `**Ticket:** tickets/NNNN-...` line is executed
by `erg-pr-merge`, not by the forge. A bare `gh pr merge` bypasses it, and the
close claim is dropped with no output — `erg check` passes either way, so a
dropped close and a clean merge leave identical evidence behind.

`/merge` is the path that honours the claim; from another checkout the bare
invocation is `~/.claude/skills/merge/erg-pr-merge -C <path> <N>`. Where this
merge goes ahead as typed, what confirms the claim landed is the ticket having
moved to `tickets/closed/` with a `Closed:` header — a green `erg check` does
not show it. A PR body carrying `Ticket: none` has nothing to lose here.
EOF
fi

exit 0
