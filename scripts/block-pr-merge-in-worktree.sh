#!/bin/bash
set -euo pipefail
# Block "gh pr merge" inside a git worktree.
#
# The `if: Bash(gh pr merge *)` gate in settings.json is NOT the filter its old
# comment here claimed. That matcher decomposes a compound command to test each
# part, and a command it cannot decompose — command substitution, a heredoc, a
# `for` loop, a subshell — it hands over anyway. So this guard receives ordinary
# work and, discarding stdin, refused it on worktree-ness alone: `erg log 0029
# "$(cat note.txt)"` was blocked with a message about `gh pr merge`, while the
# plain `erg list tickets/` beside it passed (2026-09-08). Read the command.
#
# Absent command → still fail-closed. "I could not read it" is not "it is safe";
# that is the same posture the worktree predicate below takes.

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
# the words): erring toward firing is the safe direction for the real hazard.
if [ -n "$payload" ] && [ -n "$command" ]; then
    case "$command" in
        *gh*pr*merge*) ;;
        *) exit 0 ;;
    esac
fi

# Linked-worktree predicate (ticket 0308): fire in ANY linked git worktree,
# not only harness `.claude/worktrees/<name>` ones. This guard is fail-closed
# and its whole purpose is to stop `gh pr merge`, which git aborts with
# `fatal: 'main' is already used by worktree at ...` in EVERY linked worktree
# (main's ref is locked by the primary checkout) — ad-hoc worktrees included.
# The old `[ -f .git ] && grep gitdir:` check had one real false positive: a
# submodule, whose `.git` gitdir: file points at the SUPERPROJECT but whose own
# ref-store is separate, so it shares no lock. The distinguishing test is
# git-dir vs git-common-dir: in a linked worktree the git-dir is
# `.../worktrees/<name>` under the common dir, so the two DIFFER; in the primary
# checkout and in a submodule the git-dir equals its own common dir, so they are
# EQUAL. This predicate deliberately DIFFERS from the harness-identity predicate
# used by the advisory pretooluse path guard and guard-worktree-identity.sh:
# here we want any linked worktree, not only the named harness ones.
in_worktree() {
  local git_dir common_dir
  git_dir=$(git rev-parse --absolute-git-dir 2>/dev/null) || return 1
  common_dir=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ -n "$git_dir" ] || return 1
  [ -n "$common_dir" ] || return 1
  [ "$git_dir" != "$common_dir" ]
}

if in_worktree; then
  cat >&2 <<'EOF'
Blocked: gh pr merge fails in git worktrees (main is locked by parent).
Use the GitHub API directly:

  PR=NUMBER
  gh api "repos/{owner}/{repo}/pulls/$PR/merge" -X PUT -f merge_method=squash
  gh api "repos/{owner}/{repo}/pulls/$PR" --jq .head.ref | xargs -I{} git push origin --delete {}
EOF
  exit 2
fi

exit 0
