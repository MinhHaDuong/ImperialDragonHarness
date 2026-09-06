#!/usr/bin/env bash
# Tests for scripts/sync-local-main.sh — the eager, safe local-main sync.
# Each case builds a throwaway origin + clone(s) under mktemp and asserts
# what moved and, just as important, what was left untouched.
set -euo pipefail

cd "$(dirname "$0")/.."
SYNC="$PWD/scripts/sync-local-main.sh"
fail=0

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

# Real git binary, captured before the framing shim (case 11) shadows it.
REAL_GIT=$(command -v git)
export REAL_GIT
# rtk-style output-rewrite simulator for `git worktree list --porcelain` (a
# confirmed rewrite target). Inert unless SHIM_FRAME_WORKTREE is set; then it
# frames that one subcommand's stdout — a leading banner plus a malformed,
# extra-field `branch` line — and delegates every other git call unchanged.
SHIMDIR="$SANDBOX/bin"
mkdir -p "$SHIMDIR"
cat > "$SHIMDIR/git" <<'GITSHIM'
#!/usr/bin/env bash
set -uo pipefail
: "${REAL_GIT:?REAL_GIT must point at the real git binary}"
if [[ -n "${SHIM_FRAME_WORKTREE:-}" && "${1:-}" == "worktree" && "${2:-}" == "list" ]]; then
    echo "--- Changes ---"
    "$REAL_GIT" "$@"
    echo "branch refs/heads/main is stale"
    exit 0
fi
exec "$REAL_GIT" "$@"
GITSHIM
chmod +x "$SHIMDIR/git"

_pass() { echo "PASS: $1"; }
_fail() { echo "FAIL: $1"; fail=1; }

# Build a bare origin with main at two commits, and a clone lagging one commit.
# Args: <name> → sets $ORIGIN, $CLONE, $NEW (sha the clone should reach).
_setup() {
    local name="$1"
    ORIGIN="$SANDBOX/$name-origin.git"
    CLONE="$SANDBOX/$name-clone"
    local seed="$SANDBOX/$name-seed"
    git init --quiet --bare --initial-branch=main "$ORIGIN"
    git init --quiet --initial-branch=main "$seed"
    ( cd "$seed" &&
      echo one > f.txt && git add f.txt && git commit --quiet -m c1 &&
      git remote add origin "$ORIGIN" && git push --quiet origin main )
    git clone --quiet "$ORIGIN" "$CLONE"
    ( cd "$seed" &&
      echo two > f.txt && git commit --quiet -am c2 && git push --quiet origin main )
    NEW=$(git -C "$seed" rev-parse main)
}

_main_sha() { git -C "$1" rev-parse refs/heads/main; }

# --- case 1: main checked out, clean → fast-forwarded -----------------------
_setup ff
if bash "$SYNC" "$CLONE" >/dev/null && [ "$(_main_sha "$CLONE")" = "$NEW" ]; then
    _pass "clean checked-out main is fast-forwarded"
else
    _fail "clean checked-out main should fast-forward to origin"
fi

# --- case 2: main checked out but on a feature branch → ref update,
# feature branch untouched ---------------------------------------------------
_setup ref
git -C "$CLONE" switch --quiet -c feature
feature_before=$(git -C "$CLONE" rev-parse feature)
if bash "$SYNC" "$CLONE" >/dev/null \
   && [ "$(_main_sha "$CLONE")" = "$NEW" ] \
   && [ "$(git -C "$CLONE" rev-parse feature)" = "$feature_before" ] \
   && [ "$(git -C "$CLONE" branch --show-current)" = "feature" ]; then
    _pass "main updates by ref while a feature branch is checked out; feature untouched"
else
    _fail "expected main ref update with feature branch untouched"
fi

# --- case 3: dirty overlapping file → main untouched, dirt preserved --------
_setup dirty
echo local-edit > "$CLONE/f.txt"
before=$(_main_sha "$CLONE")
out=$(bash "$SYNC" "$CLONE")
if [ "$(_main_sha "$CLONE")" = "$before" ] \
   && [ "$(cat "$CLONE/f.txt")" = "local-edit" ] \
   && echo "$out" | grep -q "left untouched"; then
    _pass "dirty overlapping file blocks the sync; dirt preserved and reported"
else
    _fail "dirty overlap must leave main and the dirty file untouched (got: $out)"
fi

# --- case 4: diverged local main → untouched, reported ----------------------
_setup diverged
( cd "$CLONE" && echo other > g.txt && git add g.txt && git commit --quiet -m local-only )
before=$(_main_sha "$CLONE")
out=$(bash "$SYNC" "$CLONE")
if [ "$(_main_sha "$CLONE")" = "$before" ] && echo "$out" | grep -q "diverged"; then
    _pass "diverged local main is reported, not moved"
else
    _fail "diverged local main must not be moved (got: $out)"
fi

# --- case 5: run from a linked worktree, main checked out in the primary →
# main is fast-forwarded across the worktree boundary, worktree untouched ----
_setup worktree
git -C "$CLONE" worktree add --quiet "$SANDBOX/worktree-wt" -b wt-branch >/dev/null
wt_before=$(git -C "$SANDBOX/worktree-wt" rev-parse wt-branch)
if bash "$SYNC" "$SANDBOX/worktree-wt" >/dev/null \
   && [ "$(_main_sha "$CLONE")" = "$NEW" ] \
   && [ "$(cat "$CLONE/f.txt")" = "two" ] \
   && [ "$(git -C "$SANDBOX/worktree-wt" rev-parse wt-branch)" = "$wt_before" ]; then
    _pass "sync from a linked worktree fast-forwards main in the primary checkout"
else
    _fail "sync from a linked worktree should ff main where it is checked out"
fi

# --- case 6: already in sync → silent, exit 0 -------------------------------
_setup silent
bash "$SYNC" "$CLONE" >/dev/null   # brings it current
out=$(bash "$SYNC" "$CLONE" 2>&1)
if [ -z "$out" ]; then
    _pass "in-sync repo produces no output"
else
    _fail "in-sync repo should be silent (got: $out)"
fi

# --- case 7: no origin remote → skip, exit 0 --------------------------------
noremote="$SANDBOX/noremote"
git init --quiet --initial-branch=main "$noremote"
( cd "$noremote" && echo x > f && git add f && git commit --quiet -m c )
if out=$(bash "$SYNC" "$noremote") && echo "$out" | grep -q "no origin"; then
    _pass "repo without origin is skipped with exit 0"
else
    _fail "repo without origin must skip cleanly"
fi

# --- case 8: not a git repo → skip, exit 0 ----------------------------------
plain="$SANDBOX/plain" && mkdir -p "$plain"
if out=$(bash "$SYNC" "$plain") && echo "$out" | grep -q "not a git repo"; then
    _pass "non-repo directory is skipped with exit 0"
else
    _fail "non-repo directory must skip cleanly"
fi

# --- case 9: nonexistent path → skip, exit 0 (exit-0 hook contract) ----------
missing="$SANDBOX/does-not-exist"
if out=$(bash "$SYNC" "$missing" 2>&1) && echo "$out" | grep -q "skipped"; then
    _pass "nonexistent path is skipped with exit 0"
else
    _fail "nonexistent path must skip cleanly (got: $out, exit $?)"
fi

# --- case 10: explicit branch argument → the NAMED branch syncs, the default
# branch is left where it was (ticket 0277) -----------------------------------
_setup brancharg
seed="$SANDBOX/brancharg-seed"
( cd "$seed" && git switch --quiet -c dev &&
  echo d1 > d.txt && git add d.txt && git commit --quiet -m d1 &&
  git push --quiet origin dev &&
  echo d2 > d.txt && git commit --quiet -am d2 && git push --quiet origin dev )
dev_new=$(git -C "$seed" rev-parse dev)
git -C "$CLONE" fetch --quiet origin dev
git -C "$CLONE" branch --quiet dev "$(git -C "$CLONE" rev-parse origin/dev^)"
main_before=$(_main_sha "$CLONE")
if bash "$SYNC" "$CLONE" dev >/dev/null \
   && [ "$(git -C "$CLONE" rev-parse refs/heads/dev)" = "$dev_new" ] \
   && [ "$(_main_sha "$CLONE")" = "$main_before" ]; then
    _pass "branch argument syncs the named branch and leaves the default branch alone"
else
    _fail "branch argument should sync only the named branch (dev)"
fi

# --- case 11: output-rewrite tolerance (ticket 0333). `git worktree list
# --porcelain` is a confirmed rtk rewrite target; the checkout-location parse
# must survive a framed stream. The shim prepends a banner and appends a
# malformed extra-field `branch refs/heads/main ...` line. Pre-fix, the loose
# awk double-emitted co_path (banner ignored, but the malformed branch line's
# $2==ref matched), corrupting it into a multi-line value so `git -C "$co_path"`
# failed and main was NOT fast-forwarded — RED. The hardened parse filters
# non-porcelain lines and requires exactly two fields on a branch record, so it
# still resolves the single real checkout and fast-forwards main.
_setup framewt
git -C "$CLONE" worktree add --quiet "$SANDBOX/framewt-wt" -b fw-branch >/dev/null
if SHIM_FRAME_WORKTREE=1 PATH="$SHIMDIR:$PATH" bash "$SYNC" "$SANDBOX/framewt-wt" >/dev/null \
   && [ "$(_main_sha "$CLONE")" = "$NEW" ]; then
    _pass "checkout-location parse survives framed worktree-list output; main fast-forwarded"
else
    _fail "framed worktree-list output corrupted the parse; main not fast-forwarded (RED = pre-fix)"
fi

# --- case 12: untracked-only checkout, no path collision → main fast-forwards
# (ticket 0851). Untracked files do not block a fast-forward, so a checkout
# carrying only untracked cruft must sync exactly like a clean one.
_setup untracked
echo cruft > "$CLONE/untracked-nocollide.txt"
out=$(bash "$SYNC" "$CLONE")
if [ "$(_main_sha "$CLONE")" = "$NEW" ] \
   && [ "$(cat "$CLONE/untracked-nocollide.txt")" = "cruft" ]; then
    _pass "untracked-only checkout fast-forwards; the untracked file survives"
else
    _fail "untracked-only checkout must fast-forward (got: $out)"
fi

# --- case 13: an untracked file collides with an incoming path → refuse, name
# the collision, overwrite nothing (ticket 0851) -----------------------------
_setup collide
( cd "$SANDBOX/collide-seed" &&
  echo incoming > new.txt && git add new.txt && git commit --quiet -m c3 &&
  git push --quiet origin main )
NEW=$(git -C "$SANDBOX/collide-seed" rev-parse main)
echo mine > "$CLONE/new.txt"
before=$(_main_sha "$CLONE")
out=$(bash "$SYNC" "$CLONE")
if [ "$(_main_sha "$CLONE")" = "$before" ] \
   && [ "$(cat "$CLONE/new.txt")" = "mine" ] \
   && echo "$out" | grep -q "untracked file"; then
    _pass "untracked/incoming collision refuses, names the collision, overwrites nothing"
else
    _fail "collision must refuse and name itself, preserving the untracked file (got: $out)"
fi

# --- case 14: tracked modifications → still refused, and named as the cause
# (ticket 0851) --------------------------------------------------------------
_setup tracked
echo local-edit > "$CLONE/f.txt"
before=$(_main_sha "$CLONE")
out=$(bash "$SYNC" "$CLONE")
if [ "$(_main_sha "$CLONE")" = "$before" ] \
   && echo "$out" | grep -q "tracked modifications" \
   && echo "$out" | grep -q "f\.txt"; then
    _pass "tracked modifications refuse the sync, named as the cause and by path"
else
    _fail "tracked modifications must be refused, named and the path listed (got: $out)"
fi

if (( fail )); then
    exit 1
fi
echo "PASS: sync-local-main moves only a fast-forwardable default branch and never touches local state, even under framed git output"
