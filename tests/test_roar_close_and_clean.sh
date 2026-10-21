#!/usr/bin/env bash
# Tests for skills/roar/close-and-clean.sh (ticket 1084).
#
# Cleanup touches only explicitly named completed-task targets. Tests run the
# real helper against temporary repositories and inject observable Git races.
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
for t in bash git jq python3 date awk grep sed sort cat mkdir rm mv ls head tail tr cut wc dirname basename realpath readlink printf env uname find xargs mktemp touch; do
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

wrapped() {
    local wd="$1"; shift
    out=$(env -i PATH="$wd:$STUBS:$TOOLS" HOME="$T" CLOSE_AND_CLEAN_ROAR_DIR="$REPO/skills/roar" IDH_ROOT="$REPO" GIT_CONFIG_GLOBAL=/dev/null bash "$SCRIPT" "$@" 2>&1) && rc=0 || rc=$?
}

# Independently selectable sections (run in parallel by test_bash_suites.py):
# cleanup (after-exit branch scoping), tickets (close, claims, preflight), exit
# (exit-check and worktree removal). Each builds its own repositories.
section_cleanup() {
# Explicit targets carry the full merged-PR head oid, obtained before cleanup.
local_target() { echo "$1=$(G rev-parse --verify "refs/heads/$1^{commit}")"; }
remote_target() { echo "$1=$(G rev-parse --verify "refs/remotes/origin/$1^{commit}")"; }

make_world "$T/scope-default" completed foreign-merged; cd "$W"
run "$SCRIPT" --phase after-exit
_check_rc "no targets: clean no-op" 0 "$rc"
_check_true "no targets: completed local remains" has_local completed
_check_true "no targets: unrelated merged local remains" has_local foreign-merged
_check_true "no targets: unrelated merged remote remains" has_remote foreign-merged

make_world "$T/scope-explicit" completed foreign-merged; cd "$W"
L=$(local_target completed); R=$(remote_target completed)
run "$SCRIPT" --phase after-exit --local-branch "$L" --remote-branch "$R"
_check_rc "explicit completed target cleans successfully" 0 "$rc"
_check_true "explicit local removed" bash -c '! git rev-parse --verify -q refs/heads/completed >/dev/null'
_check_true "explicit remote removed" bash -c '[ -z "$(git ls-remote --heads origin completed)" ]'
_check_true "foreign merged local preserved" has_local foreign-merged
_check_true "foreign merged remote preserved" has_remote foreign-merged
_check_true "default preserved" has_local main

run "$SCRIPT" --phase after-exit --local-branch "$L" --remote-branch "$R"
_check_rc "repeated cleanup is idempotent" 0 "$rc"
_check_says "already absent local reported" "$out" "ALREADY-ABSENT refs/heads/completed"
_check_says "already absent remote reported" "$out" "ALREADY-ABSENT remote refs/heads/completed"

# Remote refs outside a custom fetch refspec are inspected individually.
make_world "$T/custom-fetch" completed foreign; cd "$W"
R=$(remote_target completed)
G config --replace-all remote.origin.fetch '+refs/heads/main:refs/remotes/origin/main'
G update-ref -d refs/remotes/origin/completed
run "$SCRIPT" --phase after-exit --remote-branch "$R"
_check_rc "target beyond fetch refspec cleaned from actual remote evidence" 0 "$rc"
_check_true "custom-fetch foreign retained" has_remote foreign

# A configured fetch mapping into a local head must never move foreign work.
make_world "$T/custom-local-fetch" completed other; cd "$W"
L=$(local_target completed)
G checkout -q -b scratch; G commit -q --allow-empty -m foreign-unmerged
FOREIGN_OID=$(G rev-parse refs/heads/scratch)
G checkout -q main
G config --replace-all remote.origin.fetch '+refs/heads/other:refs/heads/scratch'
run "$SCRIPT" --phase after-exit --local-branch "$L"
_check_rc "custom local refspec: explicit cleanup completes" 0 "$rc"
_check_true "custom local refspec: unrelated unmerged local tip preserved" bash -c '[ "$(git rev-parse refs/heads/scratch)" = "$1" ]' _ "$FOREIGN_OID"
_check_true "custom local refspec: explicit target removed" bash -c '! git rev-parse --verify -q refs/heads/completed >/dev/null'

# Explicit integration fetch must also ignore opportunistic main->scratch mapping.
make_world "$T/opportunistic-local-fetch" completed; cd "$W"
L=$(local_target completed)
G checkout -q -b scratch; G commit -q --allow-empty -m foreign-unmerged
FOREIGN_OID=$(G rev-parse refs/heads/scratch)
G checkout -q main
G config --replace-all remote.origin.fetch '+refs/heads/main:refs/heads/scratch'
run "$SCRIPT" --phase after-exit --local-branch "$L"
_check_rc "opportunistic refmap: cleanup completes" 0 "$rc"
_check_true "opportunistic refmap: foreign tip preserved" bash -c '[ "$(git rev-parse refs/heads/scratch)" = "$1" ]' _ "$FOREIGN_OID"
_check_true "opportunistic refmap: explicit target removed" bash -c '! git rev-parse --verify -q refs/heads/completed >/dev/null'

# A symbolic integration tracking ref must not redirect the fetch into local work.
make_world "$T/symbolic-base" completed; cd "$W"
L=$(local_target completed)
G checkout -q -b scratch; G commit -q --allow-empty -m foreign-unmerged
FOREIGN_OID=$(G rev-parse refs/heads/scratch)
G checkout -q main
G symbolic-ref refs/remotes/origin/main refs/heads/scratch
run "$SCRIPT" --phase after-exit --local-branch "$L"
_check_rc "symbolic integration destination refuses fetch" 2 "$rc"
_check_true "symbolic integration destination preserves foreign tip" bash -c '[ "$(git rev-parse refs/heads/scratch)" = "$1" ]' _ "$FOREIGN_OID"
_check_true "symbolic integration destination preserves target" has_local completed
run "$SCRIPT" --phase after-exit --default-branch 'invalid:ref' --local-branch "$L"
_check_rc "invalid full default ref refuses fetch" 2 "$rc"
_check_true "invalid default preserves target" has_local completed

# A normal PR branch published with push -u must clean up without crashing.
make_world "$T/tracked-merged" completed foreign; cd "$W"
G push -qu origin completed
L=$(local_target completed)
run "$SCRIPT" --phase after-exit --local-branch "$L"
_check_rc "merged push-u branch cleanup succeeds" 0 "$rc"
_check_true "merged push-u local removed" bash -c '! git rev-parse --verify -q refs/heads/completed >/dev/null'
_check_true "merged push-u foreign preserved" has_local foreign
_check_lacks "merged push-u no crash" "$out" "Segmentation fault"

# A chosen HEAD-check alias already configured (fetch only, no URL) is retained.
make_world "$T/upstream-alias-collision" completed; cd "$W"
G push -qu origin completed
L=$(local_target completed)
ALIAS="idh-roar-head-check-${L#*=}"
G config "remote.$ALIAS.fetch" '+refs/heads/*:refs/remotes/alias/*'
run "$SCRIPT" --phase after-exit --local-branch "$L"
_check_rc "configured HEAD-check alias retained" 1 "$rc"
_check_true "configured HEAD-check alias preserves target" has_local completed
_check_says "configured alias retention reason" "$out" "HEAD-check alias configured"

# Multi-PR task: repetition is explicit, never repository-wide discovery.
make_world "$T/scope-multi" one two foreign; cd "$W"
run "$SCRIPT" --phase after-exit --local-branch "$(local_target one)" --local-branch "$(local_target two)"
_check_rc "multiple explicit local targets" 0 "$rc"
_check_true "both completed branches removed" bash -c '! git rev-parse --verify -q refs/heads/one >/dev/null && ! git rev-parse --verify -q refs/heads/two >/dev/null'
_check_true "multi-target foreign remains" has_local foreign
_check_true "local-only leaves remote target" has_remote one

make_world "$T/scope-protected" occupied occupied-prefix fresh; cd "$W"
G worktree add -q "$T/scope-protected/peer" occupied
G branch fresh-tip
L=$(local_target occupied); P=$(local_target occupied-prefix)
run "$SCRIPT" --phase after-exit --local-branch "$L" --remote-branch "$(remote_target occupied)" --local-branch "$P" --local-branch "$(local_target main)" --local-branch "$(local_target fresh-tip)"
_check_rc "protected targets reported as findings" 1 "$rc"
_check_says "occupied retention reason reported" "$out" "occupied worktree"
_check_says "default retention reason reported" "$out" "default branch"
_check_true "occupied branch preserved" has_local occupied
_check_true "occupied remote preserved" has_remote occupied
_check_true "whole-line occupancy permits prefix sibling cleanup" bash -c '! git rev-parse --verify -q refs/heads/occupied-prefix >/dev/null'
_check_true "default preserved when named" has_local main
_check_true "explicit completed target at integration tip eligible" bash -c '! git rev-parse --verify -q refs/heads/fresh-tip >/dev/null'
G checkout -q fresh
run "$SCRIPT" --phase after-exit --local-branch "$(local_target fresh)" --remote-branch "$(remote_target fresh)"
_check_rc "current target retained as finding" 1 "$rc"
_check_says "current retention reason reported" "$out" "current branch"
_check_true "current target local preserved" has_local fresh
_check_true "current target remote preserved" has_remote fresh

make_world "$T/scope-drift" completed; cd "$W"
L=$(local_target completed); R=$(remote_target completed)
G branch -f completed main
run "$SCRIPT" --phase after-exit --local-branch "$L" --remote-branch "$R"
_check_rc "preexisting local drift is a finding" 1 "$rc"
_check_true "drifted local retained" has_local completed
_check_says "drift reported" "$out" "DRIFT"
run "$SCRIPT" --phase after-exit --local-branch completed
_check_rc "missing expected oid rejected" 2 "$rc"
run "$SCRIPT" --phase after-exit --local-branch "completed=abcd"
_check_rc "abbreviated expected oid rejected" 2 "$rc"

make_world "$T/scope-unmerged"; cd "$W"
G checkout -q -b unmerged; G commit -q --allow-empty -m wip; G push -q origin unmerged; G checkout -q main
# Tag-shadowed base would incorrectly authorize this unmerged branch.
G tag origin/main unmerged
G branch --set-upstream-to=origin/unmerged unmerged >/dev/null
run "$SCRIPT" --phase after-exit --local-branch "$(local_target unmerged)" --remote-branch "$(remote_target unmerged)"
_check_rc "unmerged targets retained" 1 "$rc"
_check_true "unmerged local preserved" has_local unmerged
_check_true "unmerged remote preserved" has_remote unmerged

# A checkout behind integration conservatively retains a merged target.
make_world "$T/conservative"; cd "$W"
G checkout -q -b completed; G commit -q --allow-empty -m task; G push -q origin completed:main
G checkout -q -b advance; G commit -q --allow-empty -m advance; G push -q origin advance:main
G checkout -q main
run "$SCRIPT" --phase after-exit --local-branch "$(local_target completed)"
_check_rc "HEAD behind integration: Git refusal reported" 1 "$rc"
_check_true "HEAD behind integration: branch retained" has_local completed

# Inspection errors checking the alias must not be read as "unconfigured".
make_world "$T/upstream-alias-unreadable" completed; cd "$W"
G push -qu origin completed
L=$(local_target completed)
mkdir -p "$T/upstream-alias-unreadable/wrap"
cat > "$T/upstream-alias-unreadable/wrap/git" <<WRAP
#!/usr/bin/env bash
[ "\$1 \$2" = "config --get-regexp" ] && exit 128
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/upstream-alias-unreadable/wrap/git"
wrapped "$T/upstream-alias-unreadable/wrap" --phase after-exit --local-branch "$L"
_check_rc "unreadable HEAD-check alias config fails closed" 2 "$rc"
_check_true "unreadable HEAD-check alias preserves branch" has_local completed
_check_lacks "unreadable HEAD-check alias no all-clear" "$out" "RESULT: clean"

# Unexpected native failures are errors, not ordinary merge/worktree refusals.
make_world "$T/native-delete-error" completed; cd "$W"
L=$(local_target completed)
mkdir -p "$T/native-delete-error/wrap"
cat > "$T/native-delete-error/wrap/git" <<WRAP
#!/usr/bin/env bash
[[ " \$* " == *" branch -d "* ]] && exit 139
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/native-delete-error/wrap/git"
wrapped "$T/native-delete-error/wrap" --phase after-exit --local-branch "$L"
_check_rc "unexpected native delete error fails closed" 2 "$rc"
_check_says "unexpected native error reported accurately" "$out" "native deletion failed for completed (exit 139)"
_check_lacks "unexpected native error not called refusal" "$out" "Git refused deletion"
_check_lacks "unexpected native error does not assert preservation" "$out" "kept"

# Drift after ancestry must be refused before deleting, preserving config/reflog.
make_world "$T/scope-race" completed; cd "$W"
L=$(local_target completed)
B=$(G commit-tree -p completed -m wip 'completed^{tree}')
G config branch.completed.remote origin
G config core.abbrev 4
mkdir -p "$T/scope-race/wrap"
cat > "$T/scope-race/wrap/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1" = merge-base ] && [ ! -e "$T/scope-race/raced" ]; then
    : > "$T/scope-race/raced"
    "$TOOLS/git" "\$@"; rc=\$?
    "$TOOLS/git" update-ref refs/heads/completed "$B"
    exit \$rc
fi
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/scope-race/wrap/git"
wrapped "$T/scope-race/wrap" --phase after-exit --local-branch "$L"
_check_rc "local drift after ancestry refused" 1 "$rc"
_check_true "advanced tip preserved" bash -c '[ "$(git rev-parse refs/heads/completed)" = "$1" ]' _ "$B"
_check_true "upstream config preserved" bash -c '[ "$(git config branch.completed.remote)" = origin ]'
_check_true "reflog preserved" G reflog exists refs/heads/completed

# A late change at branch -d must not be allowed just because the branch
# tracks its identical remote tip. Command-local upstream is disabled, so Git tests HEAD.
make_world "$T/scope-late-drift" completed; cd "$W"
L=$(local_target completed)
B=$(G commit-tree -p completed -m wip 'completed^{tree}')
G branch --set-upstream-to=origin/completed completed >/dev/null
mkdir -p "$T/scope-late-drift/wrap"
cat > "$T/scope-late-drift/wrap/git" <<WRAP
#!/usr/bin/env bash
if [[ "\$*" == *"branch -d"* ]] && [ ! -e "$T/scope-late-drift/raced" ]; then
    : > "$T/scope-late-drift/raced"
    "$TOOLS/git" update-ref refs/heads/completed "$B"
    "$TOOLS/git" update-ref refs/remotes/origin/completed "$B"
fi
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/scope-late-drift/wrap/git"
wrapped "$T/scope-late-drift/wrap" --phase after-exit --local-branch "$L"
_check_rc "late unmerged tip tracking itself refused" 1 "$rc"
_check_lacks "late unmerged tip native refusal without crash" "$out" "Segmentation fault"
_check_true "late unmerged tip survives" bash -c '[ "$(git rev-parse refs/heads/completed)" = "$1" ]' _ "$B"
_check_true "persistent upstream unchanged" bash -c '[ "$(git config branch.completed.merge)" = refs/heads/completed ]'

# Git also refuses a peer checkout arriving after the last worktree snapshot.
make_world "$T/scope-peer-race" completed; cd "$W"
L=$(local_target completed)
mkdir -p "$T/scope-peer-race/wrap"
cat > "$T/scope-peer-race/wrap/git" <<WRAP
#!/usr/bin/env bash
if [[ " \$* " == *" branch -d "* ]] && [ ! -e "$T/scope-peer-race/raced" ]; then
    : > "$T/scope-peer-race/raced"
    "$TOOLS/git" worktree add -q "$T/scope-peer-race/peer" completed
fi
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/scope-peer-race/wrap/git"
wrapped "$T/scope-peer-race/wrap" --phase after-exit --local-branch "$L"
_check_rc "peer checkout at delete refused" 1 "$rc"
_check_true "peer branch remains" has_local completed
_check_true "peer worktree remains" test -d "$T/scope-peer-race/peer"

# Remote lease uses the previously approved oid, even after a competing push.
make_world "$T/scope-remote-race" completed; cd "$W"
R=$(remote_target completed)
B=$(G commit-tree -p completed -m wip 'completed^{tree}')
mkdir -p "$T/scope-remote-race/wrap"
cat > "$T/scope-remote-race/wrap/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1" = push ] && [ ! -e "$T/scope-remote-race/raced" ]; then
    : > "$T/scope-remote-race/raced"
    "$TOOLS/git" push -q origin "$B:refs/heads/completed"
fi
exec "$TOOLS/git" "\$@"
WRAP
chmod +x "$T/scope-remote-race/wrap/git"
wrapped "$T/scope-remote-race/wrap" --phase after-exit --remote-branch "$R"
_check_rc "remote competing push refused by lease" 1 "$rc"
_check_true "remote advanced tip survives" bash -c '[ "$(git ls-remote --heads origin completed | cut -f1)" = "$1" ]' _ "$B"

for operation in fetch worktree rev-parse show-ref ls-remote; do
    make_world "$T/unreadable-$operation" completed; cd "$W"
    L=$(local_target completed)
    mkdir -p "$T/unreadable-$operation/wrap"
    cat > "$T/unreadable-$operation/wrap/git" <<WRAP
#!/usr/bin/env bash
[ "\$1" = "$operation" ] && exit 7
exec "$TOOLS/git" "\$@"
WRAP
    chmod +x "$T/unreadable-$operation/wrap/git"
    wrapped "$T/unreadable-$operation/wrap" --phase after-exit --local-branch "$L" --remote-branch "$(remote_target completed)"
    _check_rc "unreadable $operation fails closed" 2 "$rc"
    _check_true "unreadable $operation preserves target" has_local completed
    _check_lacks "unreadable $operation no all-clear" "$out" "RESULT: clean"
done

# Local repositories use the same explicit contract without a forge.
make_world "$T/no-origin" completed foreign; cd "$W"
G remote remove origin
run "$SCRIPT" --phase after-exit --local-branch "$(local_target completed)"
_check_rc "local-only repository cleanup" 0 "$rc"
_check_true "local-only foreign remains" has_local foreign

}

section_tickets() {
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
# Failures reading either/both metadata paths must not skip the helper as
# empty==empty; dirty state and scratch must remain without an all-clear.
for metadata in both --git-dir --git-common-dir; do
    mkdir -p .panel; echo review > .panel/report.txt
    mkdir -p "$T/c19/wrap-$metadata"
    cat > "$T/c19/wrap-$metadata/git" <<WRAP
#!/usr/bin/env bash
if [ "\$1" = rev-parse ] && { [ "$metadata" = both ] || [ "\$2" = "$metadata" ]; }; then
    exit 128
fi
exec "$TOOLS/git" "\$@"
WRAP
    chmod +x "$T/c19/wrap-$metadata/git"
    wrapped "$T/c19/wrap-$metadata" --phase preflight
    _check_rc "preflight unreadable $metadata metadata fails closed" 2 "$rc"
    _check_says "preflight unreadable $metadata reported" "$out" "PREFLIGHT: COULD-NOT-LOOK"
    _check_lacks "preflight unreadable $metadata no all-clear" "$out" "RESULT: clean"
    _check_true "preflight unreadable $metadata preserves dirty state" test -f stray.txt
    _check_true "preflight unreadable $metadata never invokes scratch cleanup" test -f .panel/report.txt
done
cd "$W"

}

section_exit() {
# ── exit-check and worktree removal (ticket 1098) ───────────────────────────
# A linked worktree WT on branch <b>, one commit of work, pushed.
exit_world() { # <dir> <branch>: sets W (main checkout) and WT
    make_world "$1"; cd "$W"
    WT="$1/wt"
    G worktree add -q -b "$2" "$WT" main 2>/dev/null
    git -C "$WT" commit -q --allow-empty -m work
    git -C "$WT" push -q origin "$2"
}
merge_elsewhere() { # <branch>: merge it on origin from another clone, so W's main lags
    local c="$W/../c2"
    git clone -q "$W/../o.git" "$c" 2>/dev/null
    git -C "$c" -c user.email=t@t -c user.name=t merge -q --no-ff -m "merge $1" "origin/$1"
    git -C "$c" push -q origin main
}
# Forge stubs answer `gh pr view B --json … --jq F` by running the caller's
# real jq filter over a fixture, so the filter itself is exercised.
forge_stub() { # <dir> <pr json>
    mkdir -p "$1"
    cat > "$1/gh" <<STUB
#!/usr/bin/env bash
f=""; while [ \$# -gt 0 ]; do [ "\$1" = --jq ] && f="\$2"; shift; done
printf '%s' '$2' | jq -r "\$f"
STUB
    chmod +x "$1/gh"
}
ARMED="$T/armed";     forge_stub "$ARMED"    '{"state":"OPEN","autoMergeRequest":{"mergeMethod":"MERGE"}}'
UNARMED="$T/unarmed"; forge_stub "$UNARMED"  '{"state":"OPEN","autoMergeRequest":null}'
CLOSEDPR="$T/closed"; forge_stub "$CLOSEDPR" '{"state":"CLOSED","autoMergeRequest":{"mergeMethod":"MERGE"}}'
NOFORGE="$T/noforge"; mkdir -p "$NOFORGE"
printf '#!/usr/bin/env bash\nexit 1\n' > "$NOFORGE/gh"; chmod +x "$NOFORGE/gh"

exit_world "$T/ec-merged" task; merge_elsewhere task; cd "$WT"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check merged: ready" 0 "$rc"
_check_says "exit-check merged: verdict" "$out" "EXIT: READY"
_check_says "exit-check merged: says leave via the main checkout" "$out" "cd to the main checkout"
_check_says "exit-check merged: hands over the tree" "$out" "--remove-worktree $(cd -P "$WT" && pwd -P)"
_check_says "exit-check merged: hands over the task branch" "$out" "--local-branch task=$(git -C "$WT" rev-parse HEAD)"
_check_true "exit-check merged: local main synced to origin" \
    test "$(G rev-parse main)" = "$(G rev-parse refs/remotes/origin/main)"
# The handed-over command finishes the job from the main checkout.
cmd=$(printf '%s\n' "$out" | sed -n 's/.*then run: close-and-clean.sh //p')
cd "$W"
eval "set -- $cmd"   # the printed command is shell-quoted
run "$SCRIPT" "$@"
_check_rc "after-exit from exit-check output: clean" 0 "$rc"
_check_true "after-exit: worktree removed" test ! -d "$WT"
_check_lacks "after-exit: task branch deleted" "$(G branch --list task)" "task"

exit_world "$T/ec-unmerged" task; cd "$WT"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check unmerged: findings" 1 "$rc"
_check_says "exit-check unmerged: keep pending" "$out" "EXIT: KEEP-PENDING"
_check_lacks "exit-check unmerged: not ready" "$out" "EXIT: READY"

exit_world "$T/ec-dirty" task; merge_elsewhere task; cd "$WT"
echo stray > stray.txt
run "$SCRIPT" --phase exit-check
_check_rc "exit-check dirty: findings" 1 "$rc"
_check_says "exit-check dirty: keep pending" "$out" "EXIT: KEEP-PENDING preflight"

exit_world "$T/ec-nofetch" task; merge_elsewhere task; cd "$WT"
G remote set-url origin "$T/ec-nofetch/missing.git"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check fetch failure: could-not-look" 2 "$rc"
_check_lacks "exit-check fetch failure: no ready" "$out" "EXIT: READY"

exit_world "$T/ec-bundle" roar-wrap; cd "$WT"
wrapped "$ARMED" --phase exit-check --bundle-branch roar-wrap
_check_rc "exit-check bundle armed: ready" 0 "$rc"
_check_says "exit-check bundle armed: verdict" "$out" "EXIT: READY"
_check_lacks "exit-check bundle armed: unmerged branch not handed to cleanup" "$out" "--local-branch roar-wrap"
wrapped "$UNARMED" --phase exit-check --bundle-branch roar-wrap
_check_rc "exit-check bundle not armed: findings" 1 "$rc"
_check_says "exit-check bundle not armed: keep pending" "$out" "auto-merge armed"
wrapped "$CLOSEDPR" --phase exit-check --bundle-branch roar-wrap
_check_rc "exit-check bundle closed merge request: findings" 1 "$rc"
_check_lacks "exit-check bundle closed merge request: not ready" "$out" "EXIT: READY"
wrapped "$NOFORGE" --phase exit-check --bundle-branch roar-wrap
_check_rc "exit-check bundle unreadable forge: could-not-look" 2 "$rc"
_check_lacks "exit-check bundle unreadable forge: not ready" "$out" "EXIT: READY"
git -C "$WT" commit -q --allow-empty -m unpushed
wrapped "$ARMED" --phase exit-check --bundle-branch roar-wrap
_check_rc "exit-check bundle unpushed: findings" 1 "$rc"
_check_says "exit-check bundle unpushed: says push" "$out" "differs from HEAD"

exit_world "$T/ec-notbundle" task; cd "$WT"
wrapped "$ARMED" --phase exit-check --bundle-branch task
_check_rc "exit-check bundle name must be roar-*: findings" 1 "$rc"
_check_lacks "exit-check bundle name must be roar-*: not ready" "$out" "EXIT: READY"

cd "$W"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check outside a linked worktree: skipped" 0 "$rc"
_check_says "exit-check outside a linked worktree: says so" "$out" "not in a linked worktree"

# after-exit --remove-worktree refusals
exit_world "$T/rm-guards" task; cd "$W"
echo stray > "$WT/stray.txt"
run "$SCRIPT" --phase after-exit --remove-worktree "$WT"
_check_rc "remove dirty tree: Git refusal is a finding" 1 "$rc"
_check_true "remove dirty tree: tree kept" test -f "$WT/stray.txt"
rm "$WT/stray.txt"
run "$SCRIPT" --phase after-exit --remove-worktree "$W"
_check_rc "remove main checkout: refused" 1 "$rc"
_check_says "remove main checkout: says why" "$out" "is the main checkout"
cd "$WT"
run "$SCRIPT" --phase after-exit --remove-worktree "$WT"
_check_rc "remove current checkout: refused" 1 "$rc"
_check_says "remove current checkout: says cd out first" "$out" "cd to the main checkout first"
cd "$W"
run "$SCRIPT" --phase after-exit --remove-worktree "$T"
_check_rc "remove unregistered dir: refused" 1 "$rc"
_check_true "remove unregistered dir: untouched" test -d "$T/tools"
G worktree lock "$WT"
run "$SCRIPT" --phase after-exit --remove-worktree "$WT"
_check_rc "remove locked clean tree: removed" 0 "$rc"
_check_true "remove locked clean tree: gone" test ! -d "$WT"
_check_true "remove locked clean tree: branch kept (no target named)" has_local task

run "$SCRIPT" --phase after-exit --remove-worktree "$WT"
_check_rc "remove already-absent tree: clean" 0 "$rc"
_check_says "remove already-absent tree: reported" "$out" "WORKTREE: ALREADY-ABSENT"

# No forge: compare against the local default branch; nothing to sync.
mkdir -p "$T/ec-local"; L="$T/ec-local/repo"
git init -q -b main "$L"; git -C "$L" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
git -C "$L" worktree add -q -b task "$T/ec-local/wt" main 2>/dev/null
git -C "$T/ec-local/wt" -c user.email=t@t -c user.name=t commit -q --allow-empty -m work
cd "$T/ec-local/wt"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check no forge, unmerged: findings" 1 "$rc"
git -C "$L" -c user.email=t@t -c user.name=t merge -q --no-ff -m "merge task" task
run "$SCRIPT" --phase exit-check
_check_rc "exit-check no forge, merged: ready" 0 "$rc"
_check_says "exit-check no forge, merged: verdict" "$out" "EXIT: READY"

# Actual removal uses the same fail-closed .tmp disposal gate as GC.
git -C "$T/ec-local/repo" worktree add -q -b tmp-task "$T/ec-local/tmp-wt" main 2>/dev/null
git -C "$T/ec-local/tmp-wt" -c user.email=t@t -c user.name=t commit -q --allow-empty -m "tmp-task clean"
git -C "$T/ec-local/repo" -c user.email=t@t -c user.name=t merge -q --no-ff -m "merge tmp-task" tmp-task
python3 "$REPO/scripts/worktree-tmp-guard.py" register "$T/ec-local/tmp-wt"
mkdir -p "$T/ec-local/tmp-wt/.tmp"; echo cache > "$T/ec-local/tmp-wt/.tmp/cache.bin"
cd "$T/ec-local/repo"
run "$SCRIPT" --phase after-exit --remove-worktree "$T/ec-local/tmp-wt"
_check_rc "close-and-clean removes integrated .tmp only after citation gate" 0 "$rc"
_check_says "close-and-clean prints .tmp size before removal" "$out" "1 files"
_check_true "close-and-clean removal removes worktree-owned .tmp" test ! -d "$T/ec-local/tmp-wt"

# Author decision (ticket 1098): a main checkout parked on another branch does
# not block the exit. The tree goes; branch -d then keeps the branch, reported.
exit_world "$T/ec-parked" task; merge_elsewhere task
G switch -q -c parked
cd "$WT"
run "$SCRIPT" --phase exit-check
_check_rc "exit-check primary parked: ready" 0 "$rc"
_check_says "exit-check primary parked: notes main differs" "$out" "after-exit may keep the branch"
cmd=$(printf '%s\n' "$out" | sed -n 's/.*then run: close-and-clean.sh //p')
cd "$W"
eval "set -- $cmd"
run "$SCRIPT" "$@"
_check_rc "after-exit primary parked: finding" 1 "$rc"
_check_true "after-exit primary parked: tree removed" test ! -d "$WT"
_check_true "after-exit primary parked: branch kept, nothing lost" has_local task

# SKILL.md leaves the worktree through exit-check, cd and after-exit (step 9)
_check_true "SKILL.md step 9 runs the exit-check phase" grep -q -- '--phase exit-check' "$REPO/skills/roar/SKILL.md"

}

case "${1:-all}" in
    cleanup) section_cleanup ;;
    tickets) section_tickets ;;
    exit) section_exit ;;
    all) section_cleanup; section_tickets; section_exit ;;
    *) echo "usage: $0 [cleanup|tickets|exit|all]" >&2; exit 2 ;;
esac

exit $fail
