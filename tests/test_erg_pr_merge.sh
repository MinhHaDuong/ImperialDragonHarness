#!/usr/bin/env bash
# Regression suite for skills/merge/erg-pr-merge multi-ticket close.
#
# Builds a self-contained temp repo + git worktree, stubs `gh` on PATH with
# canned JSON, and runs the real erg-pr-merge script. Asserts that a PR body
# carrying multiple `**Ticket:**` lines closes and archives ALL of them in one
# close commit, that a single-ticket PR still works, and that a duplicated
# Ticket line does not crash (exercises the load-bearing `sort -u` dedup).
# Cases 13-14 (ticket 0200) cover the two post-push --auto/--watch races: the
# mergeability recompute race (first --auto fails "not mergeable", retried once
# after settle) and the check-registration race ("no checks reported" watch is
# retried before merging).
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
      # mergeability poll (settle_mergeable): simulate the post-push recompute
      # race — first poll reports UNKNOWN, then settles to MERGEABLE.
      if [[ "$args" == *"mergeable"* ]]; then
        if [[ -n "${STUB_MERGEABLE_UNKNOWN_ONCE:-}" ]]; then
          n=$(cat "$STUB_MERGEABLE_UNKNOWN_ONCE" 2>/dev/null || echo 0)
          if [[ "$n" -eq 0 ]]; then
            echo 1 > "$STUB_MERGEABLE_UNKNOWN_ONCE"; echo "UNKNOWN"; exit 0
          fi
        fi
        echo "MERGEABLE"; exit 0
      fi
      # merge_took_effect probe: --json state,autoMergeRequest --jq '...' →
      # emit the pre-evaluated "yes"/"no" the script's jq would produce.
      if [[ "$args" == *"autoMergeRequest"* ]]; then
        echo "${STUB_MERGE_EFFECT:-no}"; exit 0
      fi
    fi
    if [[ "$args" == *"title"* ]]; then
      jq -n --arg t "$STUB_TITLE" '{title:$t}'; exit 0
    fi
    # the big composite query
    jq -n \
      --arg n "$STUB_PR" --arg h "$STUB_BRANCH" --arg b "$STUB_BASE" \
      --arg body "$STUB_BODY" --arg draft "${STUB_IS_DRAFT:-false}" \
      '{number:($n|tonumber),headRefName:$h,baseRefName:$b,mergeable:"MERGEABLE",statusCheckRollup:[],body:$body,isDraft:($draft=="true")}'
    exit 0 ;;
  "pr ready")
    echo "$*" >> "${STUB_READY_LOG:-/dev/null}"
    echo "stub: marked ready"; exit 0 ;;
  "pr merge")
    echo "$*" >> "${STUB_MERGE_LOG:-/dev/null}"
    # Cosmetic post-action failure: gh exits non-zero on the deprecated
    # projectCards fetch AFTER the merge/queue took effect (Projects-classic).
    if [[ "${STUB_MERGE_COSMETIC_FAIL:-0}" == "1" ]]; then
      echo "GraphQL: Projects (classic) is being deprecated ... (repository.pullRequest.projectCards)" >&2
      exit 1
    fi
    if [[ "$*" == *"--auto"* ]]; then
      # Post-push recompute race: first --auto fails "not mergeable", a later
      # call (after settle_mergeable) succeeds. Distinct from STUB_AUTO_FAILS,
      # which models genuine auto-merge-unavailable on every call.
      if [[ -n "${STUB_AUTO_NOTMERGEABLE_ONCE:-}" ]]; then
        n=$(cat "$STUB_AUTO_NOTMERGEABLE_ONCE" 2>/dev/null || echo 0)
        if [[ "$n" -eq 0 ]]; then
          echo 1 > "$STUB_AUTO_NOTMERGEABLE_ONCE"
          echo "stub: Pull Request is not mergeable (mergePullRequest)" >&2
          exit 1
        fi
      fi
      if [[ "${STUB_AUTO_FAILS:-0}" == "1" ]]; then
        echo "stub: auto-merge not allowed for this repository" >&2
        exit 1
      fi
    fi
    echo "stub: merged $3"; exit 0 ;;
  "pr checks")
    echo "$*" >> "${STUB_CHECKS_LOG:-/dev/null}"
    # Check-registration race: first watch reports "no checks reported" and
    # exits non-zero instantly; a later watch passes.
    if [[ -n "${STUB_CHECKS_NOCHECKS_ONCE:-}" ]]; then
      n=$(cat "$STUB_CHECKS_NOCHECKS_ONCE" 2>/dev/null || echo 0)
      if [[ "$n" -eq 0 ]]; then
        echo 1 > "$STUB_CHECKS_NOCHECKS_ONCE"
        echo "no checks reported on the $STUB_BRANCH branch" >&2
        exit 1
      fi
    fi
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
    # Hermetic fixtures: never inherit a host's commit-signing config (a signed
    # environment otherwise fails every fixture commit with a signing error).
    git -C "$REPO" config commit.gpgsign false
    git -C "$REPO" config tag.gpgsign false
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
      STUB_AUTO_NOTMERGEABLE_ONCE="${STUB_AUTO_NOTMERGEABLE_ONCE:-}" \
      STUB_MERGEABLE_UNKNOWN_ONCE="${STUB_MERGEABLE_UNKNOWN_ONCE:-}" \
      STUB_CHECKS_NOCHECKS_ONCE="${STUB_CHECKS_NOCHECKS_ONCE:-}" \
      STUB_IS_DRAFT="${STUB_IS_DRAFT:-false}" \
      STUB_READY_LOG="${STUB_READY_LOG:-/dev/null}" \
      STUB_MERGE_COSMETIC_FAIL="${STUB_MERGE_COSMETIC_FAIL:-0}" \
      STUB_MERGE_EFFECT="${STUB_MERGE_EFFECT:-no}" \
      ERG_PR_MERGE_POLL_INTERVAL=0 \
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

# ════════════════════════════════════════════════════════════════════════════
# Case 12: closing a ticket that a sibling open ticket is Blocked-by -> the
# sibling edit `erg close` makes (strips the `Blocked-by:` line, appends a log)
# MUST be staged and committed. Path-scoping the staging to the closed ticket's
# own paths would silently drop the sibling edit when the review worktree is
# discarded — the same dirty-tree class ticket 0193 set out to fix.
# ════════════════════════════════════════════════════════════════════════════
seed_repo dependent 0220
cat > "$REPO/tickets/0221-dependent.erg" <<'ERG'
%erg 0.1
Title: Dependent ticket blocked by the one being closed
Created: 2026-06-03
Author: test
Blocked-by: 0220

--- log ---
2026-06-03T00:00Z test created

--- body ---
## Context
Open sibling whose Blocked-by must be rewritten and committed on close.
ERG
git -C "$REPO" add tickets/0221-dependent.erg
git -C "$REPO" commit -q -m "add dependent ticket"
git -C "$REPO" switch -q "$BRANCH"
git -C "$REPO" merge -q "$BASE"
BODY12=$'Summary.\n\n**Ticket:** tickets/0220-fixture.erg\n'
if run_merge "$BODY12" "ticket(0220): dependent" >/dev/null 2>&1; then
    miss=0
    closed_has 0220 || { echo "  not closed: 0220"; miss=1; }
    # The sibling's committed content on the branch must no longer carry the
    # Blocked-by line — proving the edit was staged, not silently dropped.
    if git -C "$REPO" show "$BRANCH:tickets/0221-dependent.erg" | grep -q 'Blocked-by: 0220'; then
        echo "  sibling Blocked-by edit was NOT committed (lost on worktree discard)"; miss=1
    fi
    if (( miss )); then echo "FAIL: sibling Blocked-by edit not staged on close"; fail=1
    else echo "PASS: sibling Blocked-by edit staged and committed alongside the close"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero with a dependent ticket present"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 13: post-push mergeability recompute race (ticket 0200). The close-commit
# push flips mergeable to UNKNOWN; the first `gh pr merge --auto` fails "not
# mergeable". The script must poll mergeability until it settles, retry --auto
# once (which now succeeds), and NOT fall back to watch-then-merge.
# ════════════════════════════════════════════════════════════════════════════
seed_repo recompute 0230
MLOG="$WORK/merge13.log"; CLOG="$WORK/checks13.log"
: > "$MLOG"; : > "$CLOG"
NOTMERGE_FLAG="$WORK/notmerge13"; : > "$NOTMERGE_FLAG"; echo 0 > "$NOTMERGE_FLAG"
UNKNOWN_FLAG="$WORK/unknown13"; echo 0 > "$UNKNOWN_FLAG"
BODY13=$'Summary.\n\n**Ticket:** tickets/0230-fixture.erg\n'
if STUB_AUTO_FAILS=0 STUB_MERGE_LOG="$MLOG" STUB_CHECKS_LOG="$CLOG" \
   STUB_AUTO_NOTMERGEABLE_ONCE="$NOTMERGE_FLAG" \
   STUB_MERGEABLE_UNKNOWN_ONCE="$UNKNOWN_FLAG" \
   run_merge "$BODY13" "ticket(0230): recompute" >/dev/null 2>&1; then
    rc_miss=0
    closed_has 0230 || { echo "  not closed: 0230"; rc_miss=1; }
    # --auto must have been attempted twice (initial fail + retry after settle).
    autos=$(grep -c -- '--auto' "$MLOG" || true)
    [[ "$autos" -ge 2 ]] || { echo "  expected >=2 --auto attempts, got $autos"; rc_miss=1; }
    # Must NOT have fallen back to watch-then-merge.
    grep -q -- '--watch' "$CLOG" && { echo "  fell back to watch on a transient race"; rc_miss=1; }
    if (( rc_miss )); then echo "FAIL: post-push recompute race not handled"; fail=1
    else echo "PASS: --auto retried after mergeability settles; no spurious fallback"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on post-push recompute race"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 14: fallback watch survives the no-checks-reported registration race
# (ticket 0200). Auto-merge is genuinely unavailable, so the script falls back
# to watch-then-merge. The first `gh pr checks --watch` exits non-zero with
# "no checks reported" (fresh-push registration race); the script must retry
# the watch, succeed on the second, then issue a plain --merge.
# ════════════════════════════════════════════════════════════════════════════
seed_repo registration 0231
MLOG="$WORK/merge14.log"; CLOG="$WORK/checks14.log"
: > "$MLOG"; : > "$CLOG"
NOCHECKS_FLAG="$WORK/nochecks14"; echo 0 > "$NOCHECKS_FLAG"
BODY14=$'Summary.\n\n**Ticket:** tickets/0231-fixture.erg\n'
if STUB_AUTO_FAILS=1 STUB_MERGE_LOG="$MLOG" STUB_CHECKS_LOG="$CLOG" \
   STUB_CHECKS_NOCHECKS_ONCE="$NOCHECKS_FLAG" \
   run_merge "$BODY14" "ticket(0231): registration" >/dev/null 2>&1; then
    reg_miss=0
    closed_has 0231 || { echo "  not closed: 0231"; reg_miss=1; }
    # Watch must have been retried (no-checks once, then success): >=2 watches.
    watches=$(grep -c -- '--watch' "$CLOG" || true)
    [[ "$watches" -ge 2 ]] || { echo "  expected >=2 --watch attempts, got $watches"; reg_miss=1; }
    # A plain --merge (no --auto) must follow the successful watch.
    grep -v -- '--auto' "$MLOG" | grep -q -- '--merge' \
        || { echo "  no plain --merge after fallback watch"; reg_miss=1; }
    if (( reg_miss )); then echo "FAIL: no-checks registration race not survived"; fail=1
    else echo "PASS: fallback watch retries past no-checks race, then merges"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on no-checks registration race"; fail=1
fi

# ════════════════════════════════════════════════════════════════════════════
# Case 15: draft PR (ticket 0271). Roar/raid sweeps file bootstrap PRs as draft;
# both auto-merge and the watch-then-merge fallback reject a draft. Invoking the
# script is explicit intent to merge, so it must `gh pr ready` the PR first,
# then merge and close the ticket. Anti-regression: a non-draft PR (every other
# case) must NOT call `gh pr ready`.
# ════════════════════════════════════════════════════════════════════════════
seed_repo draftcase 0271
RLOG="$WORK/ready15.log"; : > "$RLOG"
BODY15=$'Summary.\n\n**Ticket:** tickets/0271-fixture.erg\n'
if STUB_IS_DRAFT=true STUB_READY_LOG="$RLOG" \
   run_merge "$BODY15" "ticket(0271): draft" >/dev/null 2>&1; then
    d_miss=0
    closed_has 0271 || { echo "  not closed: 0271"; d_miss=1; }
    grep -q -- 'pr ready' "$RLOG" || { echo "  draft PR was not marked ready"; d_miss=1; }
    if (( d_miss )); then echo "FAIL: draft PR not readied before merge"; fail=1
    else echo "PASS: draft PR marked ready, then closed and merged"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on draft PR"; fail=1
fi

# Case 15b: a non-draft PR must NOT invoke `gh pr ready` (no over-firing).
seed_repo nondraftcase 0272
RLOG2="$WORK/ready15b.log"; : > "$RLOG2"
BODY15b=$'Summary.\n\n**Ticket:** tickets/0272-fixture.erg\n'
if STUB_IS_DRAFT=false STUB_READY_LOG="$RLOG2" \
   run_merge "$BODY15b" "ticket(0272): nondraft" >/dev/null 2>&1; then
    if grep -q -- 'pr ready' "$RLOG2"; then
        echo "FAIL: non-draft PR wrongly marked ready"; fail=1
    else echo "PASS: non-draft PR does not call gh pr ready (no over-firing)"; fi
else
    echo "FAIL: erg-pr-merge exited non-zero on non-draft PR"; fail=1
fi

# Case 16: cosmetic post-merge failure (ticket 0272). On a Projects-classic
# repo, `gh pr merge` exits non-zero on the deprecated projectCards fetch AFTER
# the merge took effect. The script must confirm the real outcome
# (merge_took_effect → MERGED) and treat it as success, not retry/abort.
# ════════════════════════════════════════════════════════════════════════════
seed_repo cosmetic 0274
BODY16=$'Summary.\n\n**Ticket:** tickets/0274-fixture.erg\n'
if STUB_MERGE_COSMETIC_FAIL=1 STUB_MERGE_EFFECT=yes \
   run_merge "$BODY16" "ticket(0274): cosmetic" >/dev/null 2>&1; then
    if closed_has 0274; then
        echo "PASS: cosmetic projectCards failure ignored when merge took effect"
    else
        echo "FAIL: cosmetic case did not close 0274"; fail=1
    fi
else
    echo "FAIL: erg-pr-merge aborted on a cosmetic post-merge gh failure"; fail=1
fi

# Case 16b: a GENUINE merge failure (gh non-zero AND PR not merged) must still
# die — merge_took_effect must not swallow real failures.
seed_repo genuinefail 0273
if STUB_MERGE_COSMETIC_FAIL=1 STUB_MERGE_EFFECT=no \
   run_merge $'Summary.\n\n**Ticket:** tickets/0273-fixture.erg\n' "ticket(0273): genuine" >/dev/null 2>&1; then
    echo "FAIL: genuine merge failure was swallowed (exited zero)"; fail=1
else
    echo "PASS: genuine merge failure still aborts (merge_took_effect=no)"
fi

if (( fail )); then exit 1; fi
echo "PASS: erg-pr-merge closes ALL Ticket lines, single-ticket unchanged, dedup safe, strays unswept, sibling edits staged, --auto/-watch races handled, drafts readied, cosmetic merge failures tolerated"
