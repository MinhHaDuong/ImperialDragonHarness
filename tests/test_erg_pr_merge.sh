#!/usr/bin/env bash
# Regression suite for skills/merge/erg-pr-merge multi-ticket close.
#
# Builds a self-contained temp repo + git worktree, stubs `gh` on PATH with
# canned JSON, and runs the real erg-pr-merge script. Asserts that a PR body
# carrying multiple `**Ticket:**` lines closes and archives ALL of them in one
# close commit, that a single-ticket PR still works, and that a duplicated
# Ticket line does not crash (exercises the load-bearing `sort -u` dedup).
set -euo pipefail
cd "$(dirname "$0")/.."
REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPT="$REPO_ROOT/skills/merge/erg-pr-merge"
ERG_BIN="$REPO_ROOT/tickets/erg"
fail=0

[[ -x "$SCRIPT" ]]  || { echo "FAIL: $SCRIPT not executable"; exit 1; }
[[ -x "$ERG_BIN" ]] || { echo "FAIL: $ERG_BIN not found";    exit 1; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# ── gh stub: dispatch by subcommand, emit canned JSON ─────────────────────────
STUBDIR="$WORK/bin"
mkdir -p "$STUBDIR"
cat > "$STUBDIR/gh" <<'STUB'
#!/usr/bin/env bash
# Canned gh: BODY and BRANCH come from the environment set by the harness.
set -euo pipefail
case "$1 $2" in
  "pr view")
    # find what --json/--jq asked for
    args="$*"
    if [[ "$args" == *"--jq"* ]]; then
      # number-only or title-only single-field --jq queries
      if [[ "$args" == *"number"* ]]; then echo "$STUB_PR"; exit 0; fi
      if [[ "$args" == *"title"*  ]]; then echo "$STUB_TITLE"; exit 0; fi
    fi
    if [[ "$args" == *"title"* ]]; then
      jq -n --arg t "$STUB_TITLE" '{title:$t}'; exit 0
    fi
    # the big composite query
    jq -n \
      --arg n "$STUB_PR" --arg h "$STUB_BRANCH" --arg b "$STUB_BASE" \
      --arg body "$STUB_BODY" \
      '{number:($n|tonumber),headRefName:$h,baseRefName:$b,mergeable:"MERGEABLE",statusCheckRollup:[],body:$body}'
    exit 0 ;;
  "pr merge")
    echo "stub: merged $3"; exit 0 ;;
  "pr checks")
    echo "stub: checks ok"; exit 0 ;;
  *)
    echo "stub gh: unexpected: $*" >&2; exit 1 ;;
esac
STUB
chmod +x "$STUBDIR/gh"

# ── seed a standalone repo with open tickets, then a PR branch ────────────────
# The real erg resolves its tickets/ dir relative to its own binary location
# (./tickets/erg → ./tickets/), so each fixture repo gets its own erg copy and
# ERG points at it. Step 4 of the script runs `git checkout <base>` here (the
# repo is not a linked worktree), so we assert on the committed branch ref —
# never the working tree.
# Sets globals: $REPO repo dir, $BRANCH the PR branch, $BASE the base branch,
# $ERG_LOCAL the per-repo erg path.
seed_repo() {
    local name="$1"; shift          # remaining args: ticket numbers to create
    REPO="$WORK/$name"
    git init -q "$REPO"
    git -C "$REPO" config user.email "test@example.com"
    git -C "$REPO" config user.name  "Test"
    mkdir -p "$REPO/tickets"
    cp "$ERG_BIN" "$REPO/tickets/erg"
    ERG_LOCAL="$REPO/tickets/erg"
    local n
    for n in "$@"; do
        cat > "$REPO/tickets/${n}-fixture.erg" <<ERG
%erg 0.1
Title: Fixture ticket ${n}
Created: 2026-06-03
Author: test

--- log ---
2026-06-03T00:00Z test created

--- body ---
## Context
Fixture for erg-pr-merge multi-close test.
ERG
    done
    git -C "$REPO" add tickets
    git -C "$REPO" commit -q -m "init: open tickets"
    # self as origin so origin/<base> resolves (script line ~99)
    git -C "$REPO" remote add origin "$REPO"
    git -C "$REPO" fetch -q origin
    BASE=$(git -C "$REPO" branch --show-current)
    BRANCH="pr-$name"
    git -C "$REPO" switch -q -c "$BRANCH"
}

run_merge() {  # $1 body, $2 title  — runs the script with cwd in the repo
    ( cd "$REPO"
      PATH="$STUBDIR:$PATH" \
      ERG="$ERG_LOCAL" \
      STUB_PR="42" STUB_BRANCH="$BRANCH" STUB_BASE="$BASE" \
      STUB_BODY="$1" STUB_TITLE="$2" \
      bash "$SCRIPT" 42 )
}

closed_has() {  # $1 ticket-number -> 0 if archived under tickets/closed/
    git -C "$REPO" ls-tree -r --name-only "$BRANCH" -- tickets/closed/ \
        | grep -q "${1}-"
}
commit_subject() { git -C "$REPO" log -1 --format=%s "$BRANCH"; }

# ════════════════════════════════════════════════════════════════════════════
# Case 1: three Ticket lines -> all three closed + commit names all three
# ════════════════════════════════════════════════════════════════════════════
seed_repo three 0181 0182 0183
BODY1=$'Summary line.\n\n**Ticket:** tickets/0181-fixture.erg\n**Ticket:** tickets/0182-fixture.erg\n**Ticket:** tickets/0183-fixture.erg\n'
if run_merge "$BODY1" "ticket(0181): multi" >/dev/null 2>&1; then
    miss=0
    for n in 0181 0182 0183; do closed_has "$n" || { echo "  not closed: $n"; miss=1; }; done
    SUBJ=$(commit_subject)
    for n in 0181 0182 0183; do [[ "$SUBJ" == *"$n"* ]] || { echo "  subject missing $n: $SUBJ"; miss=1; }; done
    if (( miss )); then echo "FAIL: multi-ticket close incomplete"; fail=1
    else echo "PASS: three Ticket lines all closed and archived; commit names all three"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on three-ticket PR"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 2: single Ticket line -> unchanged behavior
# ════════════════════════════════════════════════════════════════════════════
seed_repo single 0190
BODY2=$'Summary.\n\n**Ticket:** tickets/0190-fixture.erg\n'
if run_merge "$BODY2" "ticket(0190): solo" >/dev/null 2>&1; then
    if closed_has 0190 && [[ "$(commit_subject)" == *0190* ]]; then
        echo "PASS: single Ticket line still closes and archives (no regression)"
    else
        echo "FAIL: single-ticket close did not archive 0190"; fail=1
    fi
else
    echo "FAIL: erg-pr-merge exited non-zero on single-ticket PR"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 3: duplicated Ticket line -> dedup, no crash (exercises sort -u)
# ════════════════════════════════════════════════════════════════════════════
seed_repo dup 0195
BODY3=$'Summary.\n\n**Ticket:** tickets/0195-fixture.erg\n**Ticket:** tickets/0195-fixture.erg\n'
if run_merge "$BODY3" "ticket(0195): dup" >/dev/null 2>&1; then
    if closed_has 0195; then
        echo "PASS: duplicated Ticket line deduped, closed once, no crash"
    else
        echo "FAIL: duplicated Ticket line did not close 0195"; fail=1
    fi
else
    echo "FAIL: erg-pr-merge crashed on duplicated Ticket line"; fail=1
fi

if (( fail )); then exit 1; fi
echo "PASS: erg-pr-merge closes ALL Ticket lines, single-ticket unchanged, dedup safe"
