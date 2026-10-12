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
for t in bash git jq date awk grep sed sort cat mkdir rm mv ls head tail tr cut wc dirname basename realpath readlink printf env uname find xargs mktemp touch; do
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
# Narrowed claim: stripped alone, this guard's consequence is a bogus finding (the sweep
# tries to push-delete a branch named HEAD, which cannot exist), not a wrongful deletion.
# The abort that once skipped every later branch is the separate per-delete isolation.
_check_rc "symref control: stripped, a clean sweep turns into a false finding (rc 1)" 1 "$rc"
_check_says "symref control: …naming the bogus remote HEAD delete" "$out" "FAILED to delete remote HEAD"

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
# Three independent layers hold the current branch: guard:current, guard:worktree (it is in
# `git worktree list`) and git's own refusal inside `branch -D`. Stripping any ONE leaves it
# standing, so the per-guard control proves redundancy; the destructive control removes all three.
make_world "$T/c4" merged-a merged-b; cd "$W"
git checkout -q merged-a
run "$SCRIPT" --phase after-exit
_check_rc "current: guarded sweep exits 0" 0 "$rc"
_check_true "current: checked-out branch survives" has_local merged-a
_check_true "current: other merged branch still swept" bash -c '! git rev-parse --verify -q refs/heads/merged-b >/dev/null'
make_world "$T/c4m" merged-a merged-b; cd "$W"
git checkout -q merged-a
mutant current '/guard:current/d'
run "$MUTANT" --phase after-exit
_check_true "current control: strip guard:current alone — the worktree layer still holds it" has_local merged-a
make_world "$T/c4n" merged-a merged-b; cd "$W"
git checkout -q merged-a
mutant current3 '/guard:current/d;/guard:worktree/d;s|git branch -D -- "$b"|git update-ref -d "refs/heads/$b"|'
run "$MUTANT" --phase after-exit
_check_true "current control: all three layers stripped deletes the branch it stands on" bash -c '! git rev-parse --verify -q refs/heads/merged-a >/dev/null'

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
# Narrowed claim: git's own refusal backs this guard up, so stripped alone the consequence is a
# refused delete reported as a finding (rc 1) with the branch alive; the destruction control is
# section 16, where git's refusal is the thing removed.
mutant worktree '/guard:worktree/d'
run "$MUTANT" --phase after-exit
_check_rc "worktree control: stripped, git refuses the delete and the sweep says so (rc 1)" 1 "$rc"
_check_true "worktree control: …the other session's branch still stands" has_local merged-a

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
mutant dflag 's|git branch -D -- "$b"|git branch -d -- "$b"|'
run "$MUTANT" --phase after-exit
# Narrowed claim: this concern guards the other direction (over-retention), so its control
# shows a merged branch wrongly kept and reported as a failed delete, not a deletion.
_check_true "-D control: with -d the merged ancestor is wrongly kept" has_local ancestor
_check_rc "-D control: …and the sweep reports it as a finding (rc 1)" 1 "$rc"
# The probe half of the concern: without the ancestry test an unmerged branch is destroyed.
make_world "$T/c6p"; cd "$W"
git checkout -q -b unmerged; git commit -q --allow-empty -m wip; git push -q origin unmerged; git checkout -q main
mutant noprobe 's/git merge-base --is-ancestor "$PROBED" "$base_tip" || rc=$?/rc=0/'
run "$MUTANT" --phase after-exit
_check_true "probe control: without the ancestry test the unmerged branch is destroyed locally" bash -c '! git rev-parse --verify -q refs/heads/unmerged >/dev/null'
_check_true "probe control: …and remotely" bash -c '[ -z "$(git ls-remote --heads origin unmerged)" ]'

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
_check_rc "no ticket store: explicit skip, exit 0 (SKILL.md prerequisite policy)" 0 "$rc"
_check_says "…says it skipped" "$out" "CLOSE: skipped"
_check_says "…and the claims check skipped too" "$out" "CLAIMS: skipped"
# a ticket store that exists but cannot answer is not a repo without one
mkdir tickets
run "$SCRIPT" --phase before-exit --ticket 0001
_check_rc "tickets/ without a runnable erg exits 2" 2 "$rc"
_check_lacks "…is no all-clear" "$out" "RESULT: clean"

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
    : > "$T/c13/pushed"; "$TOOLS/git" -C "$T/c13/colleague" push -q origin merged-a
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
mutant lease 's|--force-with-lease="refs/heads/$b:$PROBED" origin ":refs/heads/$b"|origin --delete "$b"|'
env -i PATH="$T/c14/wrap:$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$MUTANT" --phase after-exit >/dev/null 2>&1 || true
_check_true "lease control: unleased delete destroys the raced commit" bash -c '! git -C "$0" ls-remote --heads origin merged-a | grep -q .' "$W"


# --- 12. the lease and the delete bind to the object id the probe approved ----
# A wrapper plays the colleague the moment the sweep's ancestry probe returns.
wrapped() { # <wrapdir> <args...>: run the real script with a git wrapper first on PATH
    local wd="$1"; shift
    out=$(env -i PATH="$wd:$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$@" 2>&1) && rc=0 || rc=$?
}
colleague() { # <dir> <branch>: a second clone of <dir>/o.git on <branch>
    git clone -q "$1/o.git" "$1/colleague" 2>/dev/null
    git -C "$1/colleague" config user.email t@t; git -C "$1/colleague" config user.name t
    git -C "$1/colleague" checkout -q "$2"
}

# 12a. approved A, then a push AND a fetch move the tracking ref to unmerged B before
# the delete: a lease read from the tracking ref afterwards would adopt B.
race_remote() { # <dir> <script>
    make_world "$1" merged-a; cd "$W"
    G branch -q -D merged-a                       # only the remote probe runs
    colleague "$1" merged-a; git -C "$1/colleague" commit -q --allow-empty -m "new work"
    mkdir -p "$1/wrap"
    cat > "$1/wrap/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1" = merge-base ] && [ ! -e "$1/raced" ]; then
    : > "$1/raced"; "$TOOLS/git" "\$@"; rc=\$?
    "$TOOLS/git" -C "$1/colleague" push -q origin merged-a
    "$TOOLS/git" -C "$W" fetch -q origin
    exit \$rc
fi
exec "$TOOLS/git" "\$@"
WRAP
    chmod +x "$1/wrap/git"
    wrapped "$1/wrap" "$2" --phase after-exit
}
race_remote "$T/c15" "$SCRIPT"
_check_rc "tracking ref moved after the probe: delete refused (rc 1)" 1 "$rc"
_check_true "…the colleague's commit survives on the remote" has_remote merged-a

# 12b. approved A, then the local branch advances to unmerged B. Real git, no mocked delete:
# the wrapper moves the ref with `update-ref` at the named trigger, then runs the real command.
#   trigger merge-base : the move lands right after the probe
#   trigger branch -D  : the move lands inside the window between the probe and git's delete
race_local() { # <dir> <script> <trigger git subcommand>
    make_world "$1" merged-a; cd "$W"
    B=$(G commit-tree -p merged-a -m wip "merged-a^{tree}")
    mkdir -p "$1/wrap"
    cat > "$1/wrap/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1 \$2" = "$3" ] && [ ! -e "$1/raced" ]; then
    : > "$1/raced"; "$TOOLS/git" -C "$W" update-ref refs/heads/merged-a $B
fi
exec "$TOOLS/git" "\$@"
WRAP
    chmod +x "$1/wrap/git"
    wrapped "$1/wrap" "$2" --phase after-exit
}
for trig in "merge-base --is-ancestor" "branch -D"; do
    race_local "$T/c16${trig%% *}" "$SCRIPT" "$trig"
    _check_rc "local branch advanced ($trig trigger): reported as a finding (rc 1)" 1 "$rc"
    _check_true "…the advanced branch survives at its new tip" bash -c '[ "$(git -C "$0" rev-parse refs/heads/merged-a)" = "$1" ]' "$W" "$B"
done
_check_says "…and the report says it was restored" "$out" "restored at"
# control: strip the restore and the same race destroys the unmerged commit
mutant norestore 's|if restore_branch "$b" "$was"; then   # guard:restore|if false; then|'
race_local "$T/c16m" "$MUTANT" "branch -D"
_check_true "restore control: without it the advanced branch is destroyed" bash -c '! git -C "$0" rev-parse --verify -q refs/heads/merged-a >/dev/null' "$W"

# --- 16. a peer checks the branch out AFTER the occupancy snapshot -------------
# The wrapper adds a real second worktree on the branch the moment the sweep calls the
# delete — after every list the script read. The branch is still at the probed commit, so a
# compare-and-set on the object id alone would succeed; git's own refusal must hold.
race_peer() { # <dir> <script>
    make_world "$1" merged-a; cd "$W"
    mkdir -p "$1/wrap"
    cat > "$1/wrap/git" <<WRAP
#!/usr/bin/env bash
if { [ "\$1 \$2" = "branch -D" ] || [ "\$1 \$2" = "update-ref -d" ]; } && [ ! -e "$1/raced" ]; then
    : > "$1/raced"; "$TOOLS/git" -C "$W" worktree add -q "$1/peer" merged-a
fi
exec "$TOOLS/git" "\$@"
WRAP
    chmod +x "$1/wrap/git"
    wrapped "$1/wrap" "$2" --phase after-exit
}
race_peer "$T/c20" "$SCRIPT"
_check_rc "peer checkout after the snapshot: delete refused, reported (rc 1)" 1 "$rc"
_check_true "…the branch under the live worktree survives" has_local merged-a
_check_true "…and the peer worktree still has it checked out" bash -c '[ "$(git -C "$0/peer" branch --show-current)" = merged-a ]' "$T/c20"
# control: the update-ref construction (compare-and-set, no worktree refusal) deletes it
mutant updateref 's|del=$(LC_ALL=C git branch -D -- "$b" 2>&1)|del=$(LC_ALL=C git update-ref -d "refs/heads/$b" "$PROBED" 2>\&1 \&\& echo "(was $PROBED)")|'
race_peer "$T/c20m" "$MUTANT"
_check_true "update-ref control: the branch is deleted from under the live worktree" bash -c '! git -C "$0" rev-parse --verify -q refs/heads/merged-a >/dev/null' "$W"
_check_true "update-ref control: …while the peer worktree exists" test -d "$T/c20m/peer"

# --- 13. enumeration failures are could-not-look, never an empty clean sweep ---
make_world "$T/c17" merged-a; cd "$W"
mkdir -p "$T/c17/wrap"
cat > "$T/c17/wrap/git" <<WRAP
#!/usr/bin/env bash
[ "\$1" = for-each-ref ] && exit 7
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/c17/wrap/git"
wrapped "$T/c17/wrap" "$SCRIPT" --phase after-exit
_check_rc "for-each-ref failing exits 2" 2 "$rc"
_check_lacks "…is no all-clear" "$out" "RESULT: clean"
_check_says "…names the failed listing" "$out" "cannot list"
_check_true "…and deleted nothing" has_local merged-a

# --- 14. a tag shadowing the integration branch cannot authorize a delete ------
# An unqualified `origin/main` resolves to refs/tags/origin/main first. The tag
# sits one commit above the unmerged branch, so against the tag it looks merged.
make_world "$T/c18"; cd "$W"
git checkout -q -b unmerged; git commit -q --allow-empty -m wip; git push -q origin unmerged
git commit -q --allow-empty -m above; git tag origin/main HEAD
git checkout -q main; git branch -q -D unmerged 2>/dev/null || git branch -q -D -f unmerged
git branch -q unmerged origin/unmerged
run "$SCRIPT" --phase after-exit --default-branch main
_check_rc "tag-shadowed base: sweep still completes (rc 0)" 0 "$rc"
_check_true "tag-shadowed base: unmerged branch survives locally" has_local unmerged
_check_true "tag-shadowed base: unmerged branch survives remotely" has_remote unmerged

# --- 15. the worktree-exit preflight runs on its own, fresh ---------------------
make_world "$T/c19"; cd "$W"
G worktree add -q -b pf "$T/c19/pf" main
cd "$T/c19/pf"
run "$SCRIPT" --phase preflight
_check_rc "preflight phase, clean worktree: rc 0" 0 "$rc"
_check_says "…ran the preflight" "$out" "PREFLIGHT: ok"
_check_lacks "…and nothing else" "$out" "SWEEP"
echo stray > stray.txt
run "$SCRIPT" --phase preflight
_check_rc "preflight phase, dirty worktree: rc 1" 1 "$rc"
_check_says "…reports DIRTY" "$out" "PREFLIGHT: DIRTY"
cd "$W"

# SKILL.md runs that fresh preflight at worktree exit (step 9a)
_check_true "SKILL.md step 9a runs the preflight phase" grep -q -- '--phase preflight' "$REPO/skills/roar/SKILL.md"

exit $fail
