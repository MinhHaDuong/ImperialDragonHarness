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
    echo "$*" >> "${STUB_MERGE_LOG:-/dev/null}"
    if [[ "$*" == *"--auto"* && "${STUB_AUTO_FAILS:-0}" == "1" ]]; then
      echo "stub: auto-merge not allowed for this repository" >&2
      exit 1
    fi
    echo "stub: merged $3"; exit 0 ;;
  "pr checks")
    echo "$*" >> "${STUB_CHECKS_LOG:-/dev/null}"
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
    # The script now pushes the close commit unconditionally (ticket 0198).
    # origin is the repo itself with $BRANCH checked out, so allow pushing to
    # the current branch of this non-bare self-origin (deviation: fixture-only).
    git -C "$REPO" config receive.denyCurrentBranch ignore
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
      STUB_AUTO_FAILS="${STUB_AUTO_FAILS:-0}" \
      STUB_MERGE_LOG="${STUB_MERGE_LOG:-/dev/null}" \
      STUB_CHECKS_LOG="${STUB_CHECKS_LOG:-/dev/null}" \
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

# ════════════════════════════════════════════════════════════════════════════
# Case 4: auto-merge happy path — queues --auto, no CI-watch poll (ticket 0198)
# ════════════════════════════════════════════════════════════════════════════
seed_repo automerge 0196
MLOG="$WORK/merge4.log"; CLOG="$WORK/checks4.log"
: > "$MLOG"; : > "$CLOG"
BODY4=$'Summary.\n\n**Ticket:** tickets/0196-fixture.erg\n'
if STUB_AUTO_FAILS=0 STUB_MERGE_LOG="$MLOG" STUB_CHECKS_LOG="$CLOG" \
   run_merge "$BODY4" "ticket(0196): auto" >/dev/null 2>&1; then
    auto_miss=0
    grep -q -- '--auto' "$MLOG" || { echo "  merge log has no --auto"; auto_miss=1; }
    grep -q -- '--watch' "$CLOG" && { echo "  checks log unexpectedly watched"; auto_miss=1; }
    if (( auto_miss )); then echo "FAIL: auto-merge happy path did not queue --auto / watched CI"; fail=1
    else echo "PASS: auto-merge queued (--auto), no CI-watch poll"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on auto-merge happy path"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 5: fallback — auto-merge disabled -> watch-then-merge (ticket 0198)
# ════════════════════════════════════════════════════════════════════════════
seed_repo fallback 0197
MLOG="$WORK/merge5.log"; CLOG="$WORK/checks5.log"
: > "$MLOG"; : > "$CLOG"
BODY5=$'Summary.\n\n**Ticket:** tickets/0197-fixture.erg\n'
if STUB_AUTO_FAILS=1 STUB_MERGE_LOG="$MLOG" STUB_CHECKS_LOG="$CLOG" \
   run_merge "$BODY5" "ticket(0197): fallback" >/dev/null 2>&1; then
    fb_miss=0
    grep -q -- '--auto' "$MLOG" || { echo "  no --auto attempt logged"; fb_miss=1; }
    grep -q -- '--watch' "$CLOG" || { echo "  fallback did not watch checks"; fb_miss=1; }
    # A bare --merge (no --auto) must have been issued after the watch.
    grep -v -- '--auto' "$MLOG" | grep -q -- '--merge' \
        || { echo "  no plain --merge after fallback"; fb_miss=1; }
    if (( fb_miss )); then echo "FAIL: fallback path incomplete"; fail=1
    else echo "PASS: fallback to watch-then-merge when auto-merge disabled"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on fallback path"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 6: close commit pushed before merge — erg-only branch (git-erg#256)
# ════════════════════════════════════════════════════════════════════════════
seed_repo strand 0199
MLOG="$WORK/merge6.log"; CLOG="$WORK/checks6.log"
: > "$MLOG"; : > "$CLOG"
BODY6=$'Summary.\n\n**Ticket:** tickets/0199-fixture.erg\n'
if STUB_AUTO_FAILS=0 STUB_MERGE_LOG="$MLOG" STUB_CHECKS_LOG="$CLOG" \
   run_merge "$BODY6" "ticket(0199): strand" >/dev/null 2>&1; then
    git -C "$REPO" rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1 \
      && git -C "$REPO" merge-base --is-ancestor "$(git -C "$REPO" rev-parse "$BRANCH")" "$(git -C "$REPO" rev-parse "origin/$BRANCH")" \
      && echo "PASS: close commit pushed before merge (no strand)" \
      || { echo "FAIL: close commit not pushed before merge"; fail=1; }
else
    echo "FAIL: erg-pr-merge exited non-zero on erg-only strand case"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 7: title-only PR — a chore(NNNN) title prefix is a SUBJECT reference,
# not a close claim. The PR must die (no close-claim in body), the seeded
# ticket must SURVIVE, and the message must name both the `none` and
# `Ticket-ref` escape hatches (ties the test to the new die message). (0199)
# ════════════════════════════════════════════════════════════════════════════
seed_repo titleonly 0216
BODY7=$'Summary only — 0216 stays open until the last two stores are done.\n'
if out=$(run_merge "$BODY7" "chore(0216): log dogfood run" 2>&1); then
    echo "FAIL: title-only PR should have died (title prefix is not a close claim)"; fail=1
else
    msg_ok=1
    echo "$out" | grep -q 'none'       || { echo "  die msg lacks 'none'";       msg_ok=0; }
    echo "$out" | grep -q 'Ticket-ref' || { echo "  die msg lacks 'Ticket-ref'"; msg_ok=0; }
    if closed_has 0216; then echo "  0216 wrongly closed by title fallback"; msg_ok=0; fi
    if (( msg_ok )); then echo "PASS: title prefix never closes; die names none/Ticket-ref; 0216 survives"
    else echo "FAIL: title-only PR did not behave per new contract"; fail=1; fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 8: `Ticket: none` — PR that closes nothing. Reaches the merge path
# (exit zero), closes no ticket. (0199)
# ════════════════════════════════════════════════════════════════════════════
seed_repo nonecase 0210
BODY8=$'Summary.\n\nTicket: none\n'
if run_merge "$BODY8" "chore: housekeeping" >/dev/null 2>&1; then
    if closed_has 0210; then echo "FAIL: Ticket: none closed 0210"; fail=1
    else echo "PASS: Ticket: none merges without closing any ticket"; fi
else
    echo "FAIL: Ticket: none should reach merge path, exited non-zero"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 9: `Ticket-ref:` — references a ticket without closing it (precedent
# PR #190 annotation idiom). Merge path reached; the referenced 0068 stays
# open. (0199)
# ════════════════════════════════════════════════════════════════════════════
seed_repo refcase 0068
BODY9=$'Summary.\n\nTicket-ref: tickets/0068-fixture.erg\n'
if run_merge "$BODY9" "chore: annotate 0068" >/dev/null 2>&1; then
    if closed_has 0068; then echo "FAIL: Ticket-ref: closed 0068"; fail=1
    else echo "PASS: Ticket-ref: references without closing; 0068 stays open"; fi
else
    echo "FAIL: Ticket-ref: should reach merge path, exited non-zero"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 10: bare `Ticket:` claim (no bold) still closes — the claim regex is
# unchanged. Anti-regression guard for the regex left intact by 0199.
# ════════════════════════════════════════════════════════════════════════════
seed_repo bareclaim 0211
BODY10=$'Summary.\n\nTicket: tickets/0211-fixture.erg\n'
if run_merge "$BODY10" "chore: bare claim" >/dev/null 2>&1; then
    if closed_has 0211; then echo "PASS: bare Ticket: claim still closes 0211 (regex unchanged)"
    else echo "FAIL: bare Ticket: claim did not close 0211"; fail=1; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on bare-claim PR"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 11: stray untracked ticket file in tickets/ -> NOT swept into the close
# commit (ticket 0193: a stash-resurrected 0149 file was swept by the blanket
# `git add tickets/` and bounced PR #242 on corpus validation)
# ════════════════════════════════════════════════════════════════════════════
seed_repo stray 0200
cat > "$REPO/tickets/0149-stray-resurrected.erg" <<'ERG'
%erg 0.1
Title: Stray file a rogue stash pop left behind
Created: 2026-05-13
Author: test

--- log ---
2026-05-13T00:00Z test created

--- body ---
## Context
Must never be staged by erg-pr-merge.
ERG
BODY11=$'Summary.\n\n**Ticket:** tickets/0200-fixture.erg\n'
if run_merge "$BODY11" "ticket(0200): stray" >/dev/null 2>&1; then
    miss=0
    closed_has 0200 || { echo "  not closed: 0200"; miss=1; }
    if git -C "$REPO" ls-tree -r --name-only "$BRANCH" | grep -q "0149-stray"; then
        echo "  stray 0149 file was swept into the close commit"; miss=1
    fi
    if (( miss )); then echo "FAIL: stray-file containment broken"; fail=1
    else echo "PASS: stray untracked ticket file left alone; close commit stages only erg-touched paths"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero with a stray file present"; fail=1
fi

if (( fail )); then exit 1; fi
echo "PASS: erg-pr-merge closes ALL Ticket lines, single-ticket unchanged, dedup safe, strays unswept"
