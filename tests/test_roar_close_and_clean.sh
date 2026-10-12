#!/usr/bin/env bash
# Tests for skills/roar/close-and-clean.sh (ticket 1084).
#
# The script folds roar steps 7-10 into one command. Its branch sweep deletes
# branches, so every guard is tested BEHAVIOURALLY: the real script runs in a
# temp repo with a bare origin, and each guard has a positive control — a copy
# of the real script with that one guard line sed-stripped, which must destroy
# something or fail. A control that is a hand-written loop would only test
# itself. Guards are tagged `# guard:<name>` in the script for this purpose.
#
# Exit codes under test: 0 clean, 1 findings, 2 could-not-look.
set -euo pipefail

# Hermetic children (ticket 0875): see tests/test_check_close_claims.sh.
export BASH_ENV=

cd "$(dirname "$0")/.."
REPO="$PWD"
SCRIPT="$REPO/skills/roar/close-and-clean.sh"
fail=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

_check_rc() { # <label> <expected> <actual>
    if [ "$2" = "$3" ]; then echo "PASS: $1"; else echo "FAIL: $1 — expected rc $2, got $3"; echo "${out:-}" | sed "s/^/    | /"; fail=1; fi
}
_check_says() { # <label> <output> <substring>
    case "$2" in *"$3"*) echo "PASS: $1" ;; *) echo "FAIL: $1 — output lacked '$3'"; fail=1 ;; esac
}
_check_lacks() { # <label> <output> <substring>
    case "$2" in *"$3"*) echo "FAIL: $1 — output carried '$3'"; fail=1 ;; *) echo "PASS: $1" ;; esac
}
_check_true() { # <label> <cmd...>
    local l="$1"; shift
    if "$@"; then echo "PASS: $l"; else echo "FAIL: $l"; fail=1; fi
}

# PATH for hermetic children: real tools by symlink, plus a gh stub. `nogh`
# omits the stub (and gh itself) for the could-not-look case.
TOOLS="$T/tools"; mkdir -p "$TOOLS"
for t in bash git jq date awk grep sed sort cat mkdir rm mv ls head tail tr cut wc dirname basename realpath readlink printf env uname find xargs mktemp; do
    p=$(command -v "$t" 2>/dev/null || true); [ -n "$p" ] && ln -sf "$p" "$TOOLS/$t"
done
STUBS="$T/stubs"; mkdir -p "$STUBS"
printf '#!/usr/bin/env bash\necho "[]"\n' > "$STUBS/gh"; chmod +x "$STUBS/gh"

run() { # <script> <args...>: hermetic run in the current directory; sets out, rc
    local s="$1"; shift
    out=$(env -i PATH="$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$s" "$@" 2>&1) && rc=0 || rc=$?
}
run_nogh() {
    local s="$1"; shift
    out=$(env -i PATH="$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$s" "$@" 2>&1) && rc=0 || rc=$?
}

# A copy of the real script with every line tagged `# guard:<name>` removed
# (or an arbitrary sed expression applied), in a temp dir; run() points CLOSE_AND_CLEAN_ROAR_DIR
# at the real skill directory so the copy still finds its helpers.
mutant() { # <name> <sed-expr>
    mkdir -p "$T/mutants"
    local m="$T/mutants/$1.sh"
    sed "$2" "$SCRIPT" > "$m"
    cmp -s "$SCRIPT" "$m" && { echo "FAIL: mutation '$2' changed nothing"; fail=1; }
    MUTANT="$m"
}

G() { git -C "$W" "$@"; }
make_world() { # <dir>: bare origin + clone; sets W. Branches given as args are merged into main and pushed.
    local d="$1"; shift
    mkdir -p "$d"; W="$d/w"
    git init -q --bare -b main "$d/o.git"
    git clone -q "$d/o.git" "$W" 2>/dev/null
    G config user.email t@t; G config user.name t
    G commit -q --allow-empty -m init; G branch -M main
    G push -q origin main
    for b in "$@"; do G branch "$b"; G push -q origin "$b"; done
    # Main moves past the branches: a branch AT main's tip carries no work and is kept.
    G commit -q --allow-empty -m advance; G push -q origin main
    G remote set-head origin main >/dev/null
}
has_local() { git -C "$W" rev-parse --verify -q "refs/heads/$1" >/dev/null; }
has_remote() { [ -n "$(git -C "$W" ls-remote --heads origin "$1")" ]; }

# --- 1. basic sweep: the first test, fails while the script is absent -------
make_world "$T/c1" merged-a merged-b
cd "$W"
run "$SCRIPT" --phase after-exit
_check_rc "clean sweep exits 0" 0 "$rc"
_check_true "merged-a swept locally" bash -c '! git rev-parse --verify -q refs/heads/merged-a >/dev/null'
_check_true "merged-b swept remotely" bash -c '[ -z "$(git ls-remote --heads origin merged-b)" ]'
_check_true "main survives" has_local main
_check_says "reports a result line" "$out" "RESULT: clean"

# --- 2. guard: origin/HEAD symref --------------------------------------------
# origin/HEAD points at `trunk`, an ancestor strictly behind main: without the guard
# the sweep tries to delete the symref itself.
make_world "$T/c2" merged-a merged-b trunk; cd "$W"
G remote set-head origin trunk >/dev/null
run "$SCRIPT" --phase after-exit --default-branch main
_check_rc "symref: guarded sweep exits 0" 0 "$rc"
_check_true "symref: origin/merged-b removed past the symref" bash -c '[ -z "$(git ls-remote --heads origin merged-b)" ]'
_check_true "symref: origin/main survives" has_remote main
make_world "$T/c2m" merged-a merged-b trunk; cd "$W"
G remote set-head origin trunk >/dev/null
mutant symref '/guard:symref/d'
run "$MUTANT" --phase after-exit --default-branch main
_check_true "symref control: unguarded sweep does not exit 0" test "$rc" != 0

# --- 3. guard: main survives a detached primary checkout ---------------------
make_world "$T/c3" merged-a; cd "$W"
git checkout -q --detach; git branch -f main HEAD~1   # main behind origin/main: an ancestor, not the tip
run "$SCRIPT" --phase after-exit
_check_rc "detached: guarded sweep exits 0" 0 "$rc"
_check_true "detached: main survives" has_local main
make_world "$T/c3m" merged-a; cd "$W"
git checkout -q --detach; git branch -f main HEAD~1
mutant default '/guard:default/d'
run "$MUTANT" --phase after-exit
_check_true "default-branch control: main is destroyed" bash -c '! git rev-parse --verify -q refs/heads/main >/dev/null'

# --- 4. guard: current branch ------------------------------------------------
# The current branch is also in `git worktree list`, so the worktree guard
# covers it too; the control strips both to show what git alone does.
make_world "$T/c4" merged-a merged-b; cd "$W"
git checkout -q merged-a
run "$SCRIPT" --phase after-exit
_check_rc "current: guarded sweep exits 0" 0 "$rc"
_check_true "current: checked-out branch survives" has_local merged-a
_check_true "current: other merged branch still swept" bash -c '! git rev-parse --verify -q refs/heads/merged-b >/dev/null'
make_world "$T/c4m" merged-a merged-b; cd "$W"
git checkout -q merged-a
mutant current '/guard:current/d;/guard:worktree/d'
run "$MUTANT" --phase after-exit
_check_rc "current control: unguarded sweep hits git's refusal (rc 1)" 1 "$rc"

# --- 5. guard: branch checked out in another worktree, whole-line match ------
make_world "$T/c5" merged-a merged-a-2 merged-b; cd "$W"
git worktree add -q "$T/c5/x" merged-a
run "$SCRIPT" --phase after-exit
_check_rc "worktree: guarded sweep exits 0" 0 "$rc"
_check_true "worktree: other session's branch survives" has_local merged-a
_check_true "worktree: prefix-sharing merged-a-2 is NOT protected" bash -c '! git rev-parse --verify -q refs/heads/merged-a-2 >/dev/null'
_check_true "worktree: later branch merged-b still swept" bash -c '! git rev-parse --verify -q refs/heads/merged-b >/dev/null'
make_world "$T/c5m" merged-a merged-b; cd "$W"
git worktree add -q "$T/c5m/x" merged-a
mutant worktree '/guard:worktree/d'
run "$MUTANT" --phase after-exit
_check_rc "worktree control: unguarded sweep fails (rc 1)" 1 "$rc"

# --- 6. -D after the ancestry probe; unmerged survives -----------------------
make_world "$T/c6"; cd "$W"
git checkout -q -b ancestor; git commit -q --allow-empty -m side
git push -q origin ancestor:main            # origin/main now contains `ancestor`
git checkout -q -b adv; git commit -q --allow-empty -m adv; git push -q origin adv:main
git checkout -q main; git branch -q -D adv   # HEAD does not contain `ancestor`: -d would refuse
git checkout -q -b unmerged; git commit -q --allow-empty -m wip
git push -q origin unmerged
git checkout -q main
run "$SCRIPT" --phase after-exit
_check_rc "ancestor: sweep exits 0" 0 "$rc"
_check_true "ancestor: deleted despite -d refusing" bash -c '! git rev-parse --verify -q refs/heads/ancestor >/dev/null'
_check_true "unmerged: local survives" has_local unmerged
_check_true "unmerged: remote survives" has_remote unmerged
make_world "$T/c6m"; cd "$W"
git checkout -q -b ancestor; git commit -q --allow-empty -m side
git push -q origin ancestor:main
git checkout -q -b adv; git commit -q --allow-empty -m adv; git push -q origin adv:main
git checkout -q main; git branch -q -D adv
mutant dflag 's/branch -D/branch -d/'
run "$MUTANT" --phase after-exit
_check_true "-D control: with -d the ancestor survives" has_local ancestor

# --- 7. could-not-look is exit 2, never an all-clear -------------------------
make_world "$T/c7" merged-a; cd "$W"
git remote set-url origin "$T/does-not-exist.git"
run "$SCRIPT" --phase after-exit
_check_rc "failed fetch exits 2" 2 "$rc"
_check_lacks "failed fetch is no all-clear" "$out" "RESULT: clean"
_check_true "failed fetch deletes nothing" has_local merged-a

# no tickets/erg at all (the aedist-technical-report case)
make_world "$T/c9"; cd "$W"
run "$SCRIPT" --phase before-exit --ticket 0001
_check_rc "no tickets/erg exits 2" 2 "$rc"
_check_lacks "no tickets/erg is no all-clear" "$out" "RESULT: clean"

# --- 10. ticket close, claims, tracker detection -----------------------------
ticket_world() { # <dir>
    make_world "$1"; cd "$W"
    mkdir -p tickets/closed
    cp "$REPO/tickets/erg" "$REPO/tickets/.ergrc" tickets/
    printf '%%erg 0.1\nTitle: parent\nCreated: 2026-10-01\nAuthor: t\n\n--- log ---\n\n--- body ---\n' > tickets/0100-parent.erg
    printf '%%erg 0.1\nTitle: child one\nCreated: 2026-10-01\nAuthor: t\nParent: 0100\n\n--- log ---\n\n--- body ---\n' > tickets/0101-one.erg
    printf '%%erg 0.1\nTitle: child two\nCreated: 2026-10-01\nAuthor: t\nParent: 0100\nClosed: 2026-10-02 done\n\n--- log ---\n\n--- body ---\n' > tickets/0102-two.erg
    G add -A; G commit -q -m tickets; G push -q origin main
}
# the forge case must reach the forge: a real ticket store, no gh on PATH
ticket_world "$T/c8"
run_nogh "$SCRIPT" --phase before-exit
_check_rc "no forge CLI exits 2" 2 "$rc"
_check_says "…reached the claims check" "$out" "CLAIMS: COULD-NOT-LOOK (exit"
_check_lacks "no forge CLI is no all-clear" "$out" "RESULT: clean"

run "$SCRIPT" --ticket
_check_rc "an option missing its value exits 2" 2 "$rc"

# a branch AT main's tip (a colleague's just-created branch) is kept, locally and remotely
make_world "$T/c12"; cd "$W"
G branch fresh; G push -q origin fresh
run "$SCRIPT" --phase after-exit
_check_rc "tip-of-main branch: sweep exits 0" 0 "$rc"
_check_true "tip-of-main branch kept locally" has_local fresh
_check_true "tip-of-main branch kept remotely" has_remote fresh

ticket_world "$T/c10"
run "$SCRIPT" --phase before-exit --ticket 0101
_check_rc "open ticket closed: finding, rc 1" 1 "$rc"
_check_says "reports CLOSED-UNCOMMITTED" "$out" "CLOSED-UNCOMMITTED 0101"
_check_says "last sibling closed: integration review due" "$out" "INTEGRATION-REVIEW-DUE 0100"
run "$SCRIPT" --phase before-exit --ticket 0101
_check_says "second run: ALREADY-CLOSED" "$out" "ALREADY-CLOSED 0101"

ticket_world "$T/c11"
printf '%%erg 0.1\nTitle: child three\nCreated: 2026-10-01\nAuthor: t\nParent: 0100\n\n--- log ---\n\n--- body ---\n' > tickets/0103-three.erg
G add -A; G commit -q -m c3
run "$SCRIPT" --phase before-exit --ticket 0101
_check_lacks "open sibling: no integration review" "$out" "INTEGRATION-REVIEW-DUE"
_check_true "tracker detection never exits 2" test "$rc" != 2

# --- 11. remote delete is leased to the probed commit -------------------------
# A colleague pushes to a merged branch AFTER the sweep's fetch: the delete must
# be refused, not destroy their commit. A git wrapper on PATH plays the colleague
# the moment the sweep pushes.
make_world "$T/c13" merged-a; cd "$W"
git clone -q "$T/c13/o.git" "$T/c13/colleague" 2>/dev/null
git -C "$T/c13/colleague" config user.email t@t; git -C "$T/c13/colleague" config user.name t
git -C "$T/c13/colleague" checkout -q merged-a; git -C "$T/c13/colleague" commit -q --allow-empty -m "new work"
mkdir -p "$T/c13/wrap"
cat > "$T/c13/wrap/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1" = push ] && [ ! -e "$T/c13/pushed" ]; then
    touch "$T/c13/pushed"; "$TOOLS/git" -C "$T/c13/colleague" push -q origin merged-a
fi
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/c13/wrap/git"
out=$(env -i PATH="$T/c13/wrap:$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$SCRIPT" --phase after-exit 2>&1) && rc=0 || rc=$?
_check_rc "raced remote delete is refused (rc 1)" 1 "$rc"
_check_true "colleague's new commit survives on the remote" has_remote merged-a

# control: without the lease the same race destroys the colleague's commit
make_world "$T/c14" merged-a; cd "$W"
git clone -q "$T/c14/o.git" "$T/c14/colleague" 2>/dev/null
git -C "$T/c14/colleague" config user.email t@t; git -C "$T/c14/colleague" config user.name t
git -C "$T/c14/colleague" checkout -q merged-a; git -C "$T/c14/colleague" commit -q --allow-empty -m "new work"
mkdir -p "$T/c14/wrap"
sed "s/c13/c14/g" "$T/c13/wrap/git" > "$T/c14/wrap/git"; chmod +x "$T/c14/wrap/git"
mutant lease 's/--force-with-lease="[^"]*(")" origin/origin/;s|--force-with-lease="refs/heads/\$b:\$(git rev-parse "refs/remotes/origin/\$b")" origin ":refs/heads/\$b"|origin --delete "$b"|'
env -i PATH="$T/c14/wrap:$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$MUTANT" --phase after-exit >/dev/null 2>&1 || true
_check_true "lease control: unleased delete destroys the raced commit" bash -c '! git -C "$0" ls-remote --heads origin merged-a | grep -q .' "$W"

exit $fail
