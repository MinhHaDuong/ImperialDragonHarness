#!/usr/bin/env bash
# check-primary-checkout.sh — detect a stranded primary checkout (ticket 0247).
#
# A checkout is "stranded" when it sits off the default branch, or carries a
# dirty working tree beyond a locally-modified settings.json. A dream run that
# dies between its consolidation commit and the push+PR leaves exactly this
# state: the primary parked on a `dream-consolidate-*` branch with a dirty tree,
# which blocks the daily-pull timer and beat's dirty-tree pre-flight for days.
#
# Silent + exit 0 when the checkout is on <default-branch> and clean.
# Prints a STRANDED: reason to stdout and exits 1 otherwise.
#
# Usage: check-primary-checkout.sh [REPO_DIR] [DEFAULT_BRANCH]
#   REPO_DIR        defaults to $HOME/.claude
#   DEFAULT_BRANCH  defaults to main
set -euo pipefail

REPO="${1:-$HOME/.claude}"
DEFAULT_BRANCH="${2:-main}"

if ! git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  echo "STRANDED: $REPO is not a git repository"
  exit 1
fi

# A detached HEAD prints "HEAD" here — not the default branch, so flagged.
branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
if [ "$branch" != "$DEFAULT_BRANCH" ]; then
  echo "STRANDED: $REPO is off $DEFAULT_BRANCH (on $branch)"
  exit 1
fi

# Tolerate a locally-modified settings.json; flag any other dirt (tracked or
# untracked). Whitelist-ignored files never appear in porcelain output, so this
# keys on visible working-tree changes only. Capture git status separately so a
# real status failure aborts under set -e instead of being read as "clean"; the
# trailing `|| true` guards only grep's no-match exit. quotePath=false keeps
# non-ASCII paths unquoted so the exact-match whitelist behaves predictably.
status="$(git -C "$REPO" -c core.quotePath=false status --porcelain)"
dirty="$(printf '%s\n' "$status" | awk 'NF { print substr($0, 4) }' | grep -vx 'settings.json' || true)"
if [ -n "$dirty" ]; then
  echo "STRANDED: $REPO has a dirty working tree beyond settings.json:"
  echo "$dirty"
  exit 1
fi

exit 0
