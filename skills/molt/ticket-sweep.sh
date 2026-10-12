#!/usr/bin/env bash
# Ticket close / archive / merged-branch probe for /molt and /healthcheck.
#
#   ticket-sweep.sh close <id>           close an open ticket as already-done, stage it
#   ticket-sweep.sh archive              archive closed tickets, prune duplicates, stage
#   ticket-sweep.sh merged-probe <branch>  exit 0 merged, 1 not merged, 2 could not determine
#
# Acts on the current repository. The erg binary is ${MOLT_ERG:-tickets/erg}.
# Every subcommand exits 2 when tickets/ or the erg binary is missing: callers
# must read 2 as "could not look" and skip the destructive step it guards.
set -euo pipefail

ERG=${MOLT_ERG:-tickets/erg}

cannot_look() {
  echo "could-not-determine: $1" >&2
  echo "could-not-determine"
  exit 2
}

[ -d tickets ] || cannot_look "no tickets/ directory"
[ -x "$ERG" ] || cannot_look "erg binary $ERG not executable"

cmd_close() {
  local id=${1:?usage: close <id>} source destination
  source=$(find tickets -maxdepth 1 -type f -name "${id}-*.erg" -print -quit)
  [ -n "$source" ] || { echo "No open ticket file for $id" >&2; exit 1; }
  "$ERG" close "$id" already-done tickets/
  git add -u -- "$source"
  destination="tickets/closed/$(basename "$source")"
  [ ! -f "$destination" ] || git add -- "$destination"
}

cmd_archive() {
  local archive_output line source destination f
  # Older erg moves files here; current erg may already have moved them on
  # close. Stage only paths reported by this archive call.
  archive_output=$("$ERG" archive tickets/ 2>/dev/null) || true
  while IFS= read -r line; do
    case "$line" in
      "ARCHIVED "*)
        source="tickets/${line#ARCHIVED }"
        if git ls-files --error-unmatch -- "$source" >/dev/null 2>&1; then
          git add -u -- "$source"
        fi
        destination="tickets/closed/$(basename "$source")"
        [ ! -f "$destination" ] || git add -- "$destination"
        ;;
    esac
  done <<< "$archive_output"
  # Duplicate committed under both paths, possible independently of the archive.
  for f in tickets/*.erg; do
    [ -e "$f" ] || continue
    if [ -f "tickets/closed/$(basename "$f")" ]; then
      git rm -- "$f" >/dev/null
    fi
  done
}

cmd_merged_probe() {
  local branch=${1:?usage: merged-probe <branch>} num ticket pr subjects
  # Signal A: ancestry (merge commits and fast-forwards).
  if git merge-base --is-ancestor "$branch" main 2>/dev/null; then
    return 0
  fi
  # Signal B: squash merges leave no ancestry; look for "(#N)" in main's
  # subjects, with N taken from the closed ticket's Closed: header.
  [[ $branch =~ ^t([0-9]+) ]] || cannot_look "branch $branch does not map to a ticket"
  num=$(printf '%04d' "$((10#${BASH_REMATCH[1]}))")
  ticket=$(compgen -G "tickets/closed/${num}-*" | head -n 1 || true)
  [ -n "$ticket" ] || cannot_look "no closed ticket $num"
  pr=$(sed -nE 's/^Closed:.*#([0-9]+).*/\1/p' "$ticket" | head -n 1)
  [ -n "$pr" ] || cannot_look "ticket $num has no PR number in Closed:"
  # Capture first: grep -q exiting early would SIGPIPE git log under pipefail.
  subjects=$(git log main --format=%s)
  if grep -qE "\(#${pr}\)" <<< "$subjects"; then
    return 0
  fi
  return 1
}

case "${1:-}" in
  close) shift; cmd_close "$@" ;;
  archive) cmd_archive ;;
  merged-probe) shift; cmd_merged_probe "$@" ;;
  *) echo "usage: ticket-sweep.sh close <id> | archive | merged-probe <branch>" >&2; exit 64 ;;
esac
