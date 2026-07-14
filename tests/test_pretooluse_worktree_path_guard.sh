#!/usr/bin/env bash
# Tests for scripts/pretooluse-worktree-path-guard.sh
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/pretooluse-worktree-path-guard.sh"
fail=0

PRIMARY="/home/testuser/repo"
WORKTREE="/home/testuser/repo/.worktrees/t001"

_payload() {
    local fp="$1"
    printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"}}' "$fp"
}

_payload_with_cwd() {
    local fp="$1" cwd="$2"
    printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"},"cwd":"%s"}' "$fp" "$cwd"
}

# NotebookEdit carries its target in notebook_path (not file_path). The
# settings.json matcher includes NotebookEdit, so the guard must read it too.
_payload_notebook() {
    local np="$1"
    printf '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"%s","new_source":"x"}}' "$np"
}

_run_hook_notebook() {
    local wt="$1" pr="$2" np="$3"
    _payload_notebook "$np" | env _GUARD_WORKTREE_ROOT="$wt" _GUARD_PRIMARY_ROOT="$pr" bash "$HOOK" 2>&1 || true
}

_rc_notebook() {
    local wt="$1" pr="$2" np="$3"
    _payload_notebook "$np" \
        | env _GUARD_WORKTREE_ROOT="$wt" _GUARD_PRIMARY_ROOT="$pr" bash "$HOOK" \
            >/dev/null 2>&1 && echo 0 || echo $?
}

_run_hook() {
    local wt="$1" pr="$2" fp="$3"
    _payload "$fp" | env _GUARD_WORKTREE_ROOT="$wt" _GUARD_PRIMARY_ROOT="$pr" bash "$HOOK" 2>&1 || true
}

_run_hook_with_cwd() {
    local wt="$1" pr="$2" fp="$3" cwd="$4"
    _payload_with_cwd "$fp" "$cwd" \
        | env _GUARD_WORKTREE_ROOT="$wt" _GUARD_PRIMARY_ROOT="$pr" bash "$HOOK" 2>&1 || true
}

# Return the guard's exit code (not its output), so a deny (exit 2) is
# distinguishable from an advisory-then-allow (exit 0). Extra env pairs after
# the payload args are passed through to the hook (used for GUARD_ALLOW_PRIMARY_EDIT).
_rc() {
    local wt="$1" pr="$2" fp="$3"; shift 3
    _payload "$fp" \
        | env _GUARD_WORKTREE_ROOT="$wt" _GUARD_PRIMARY_ROOT="$pr" "$@" bash "$HOOK" \
            >/dev/null 2>&1 && echo 0 || echo $?
}

# 1. Main-repo path while in worktree → deny (exit 2) with a corrective message
out=$(_run_hook "$WORKTREE" "$PRIMARY" "$PRIMARY/src/main.py")
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: warns on main-repo path"
else
    echo "FAIL: expected warning for main-repo path; got: $out"
    fail=1
fi
rc=$(_rc "$WORKTREE" "$PRIMARY" "$PRIMARY/src/main.py")
if [ "$rc" = "2" ]; then
    echo "PASS: denies (exit 2) on main-repo path"
else
    echo "FAIL: expected exit 2 for main-repo path; got: $rc"
    fail=1
fi

# 2. Worktree-rooted path → silent
out=$(_run_hook "$WORKTREE" "$PRIMARY" "$WORKTREE/src/main.py")
if [ -z "$out" ]; then
    echo "PASS: silent for worktree-rooted path"
else
    echo "FAIL: unexpected output for worktree path: $out"
    fail=1
fi

# 3. Path outside both roots → silent
out=$(_run_hook "$WORKTREE" "$PRIMARY" "/tmp/unrelated/file.py")
if [ -z "$out" ]; then
    echo "PASS: silent for unrelated path"
else
    echo "FAIL: unexpected output for unrelated path: $out"
    fail=1
fi

# 4. No worktree active → silent. Hermetic fixture: a temp dir whose cwd has
# .git as a real DIRECTORY (not a gitdir: pointer file), so the guard's
# _in_worktree() returns false regardless of where the suite itself runs from
# (a linked worktree's .git is a file, which would otherwise trip detection).
_case4_dir=$(mktemp -d)
mkdir "$_case4_dir/.git"
out=$( cd "$_case4_dir" && echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/unrelated/file.py","content":"x"}}' \
      | bash "$HOOK" 2>&1 || true)
rm -rf "$_case4_dir"
if [ -z "$out" ]; then
    echo "PASS: silent when not in a worktree"
else
    echo "FAIL: unexpected output when no worktree: $out"
    fail=1
fi

# 5. Missing file_path field → silent
out=$(_payload "" | env _GUARD_WORKTREE_ROOT="$WORKTREE" _GUARD_PRIMARY_ROOT="$PRIMARY" bash "$HOOK" 2>&1 || true)
if [ -z "$out" ]; then
    echo "PASS: silent when no file_path in payload"
else
    echo "FAIL: unexpected output when no file_path: $out"
    fail=1
fi

# 6. Relative file_path + .cwd inside primary repo → warn (resolves against .cwd,
# not the hook's $(pwd)). Regression test for ticket 0173.
out=$(_run_hook_with_cwd "$WORKTREE" "$PRIMARY" "src/main.py" "$PRIMARY")
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: warns on relative path resolved via .cwd into primary repo"
else
    echo "FAIL: expected warning for relative path with .cwd=primary; got: $out"
    fail=1
fi

# 7. Relative file_path + .cwd inside worktree → silent (already inside worktree).
out=$(_run_hook_with_cwd "$WORKTREE" "$PRIMARY" "src/main.py" "$WORKTREE")
if [ -z "$out" ]; then
    echo "PASS: silent for relative path resolved via .cwd into worktree"
else
    echo "FAIL: unexpected output for relative path with .cwd=worktree: $out"
    fail=1
fi

# 8. Real worktree OUTSIDE .claude/worktrees/ (submodule / ad-hoc worktree) →
# silent. The weak `[ -f .git ]` predicate warned here (false positive on any
# gitdir: file); the identity predicate keys on the .claude/worktrees/<name>
# path segment, so an out-of-convention tree goes silent. Regression for
# ticket 0308. Exercises the real-git identity-resolution path (no env override).
_case8_primary=$(mktemp -d)
git -C "$_case8_primary" init -q
git -C "$_case8_primary" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
git -C "$_case8_primary" worktree add -q "$_case8_primary/adhoc"
out=$( cd "$_case8_primary/adhoc" \
       && printf '{"tool_name":"Write","tool_input":{"file_path":"%s/src/main.py","content":"x"}}' "$_case8_primary" \
       | bash "$HOOK" 2>&1 || true)
git -C "$_case8_primary" worktree remove --force "$_case8_primary/adhoc" 2>/dev/null || true
rm -rf "$_case8_primary"
if [ -z "$out" ]; then
    echo "PASS: silent in a worktree outside .claude/worktrees/ (identity predicate)"
else
    echo "FAIL: expected silence for non-harness worktree; got: $out"
    fail=1
fi

# 9. Real harness worktree (.claude/worktrees/<name>) → still warns on a
# main-repo path. Positive companion to case 8: the tightened predicate keeps
# firing where it should.
_case9_primary=$(mktemp -d)
git -C "$_case9_primary" init -q
git -C "$_case9_primary" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
mkdir -p "$_case9_primary/.claude/worktrees"
git -C "$_case9_primary" worktree add -q "$_case9_primary/.claude/worktrees/t001"
out=$( cd "$_case9_primary/.claude/worktrees/t001" \
       && printf '{"tool_name":"Write","tool_input":{"file_path":"%s/src/main.py","content":"x"}}' "$_case9_primary" \
       | bash "$HOOK" 2>&1 || true)
git -C "$_case9_primary" worktree remove --force "$_case9_primary/.claude/worktrees/t001" 2>/dev/null || true
rm -rf "$_case9_primary"
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: warns in a real harness worktree (identity predicate positive)"
else
    echo "FAIL: expected warning in harness worktree; got: $out"
    fail=1
fi

# 10. Memory-dir exemption: projects/*/memory/** in the primary checkout is
# written directly by absolute path by design (the primary .gitignore whitelist
# tracks it; skills/memory tells every session to write it there). Not denied.
rc=$(_rc "$WORKTREE" "$PRIMARY" "$PRIMARY/projects/-home-haduong--claude/memory/MEMORY.md")
if [ "$rc" = "0" ]; then
    echo "PASS: exempts primary projects/*/memory/** path (exit 0)"
else
    echo "FAIL: expected exit 0 for memory-dir path; got: $rc"
    fail=1
fi
out=$(_run_hook "$WORKTREE" "$PRIMARY" "$PRIMARY/projects/-home-haduong--claude/memory/MEMORY.md")
if [ -z "$out" ]; then
    echo "PASS: silent for memory-dir path"
else
    echo "FAIL: unexpected output for memory-dir path: $out"
    fail=1
fi

# 11. Escape hatch: GUARD_ALLOW_PRIMARY_EDIT set → intentional primary edit is
# allowed. A human pre-authorizes by exporting it BEFORE session start; the hook
# is spawned by the CLI, so an agent cannot set it mid-turn.
rc=$(_rc "$WORKTREE" "$PRIMARY" "$PRIMARY/src/main.py" GUARD_ALLOW_PRIMARY_EDIT=1)
if [ "$rc" = "0" ]; then
    echo "PASS: escape hatch allows primary edit (exit 0)"
else
    echo "FAIL: expected exit 0 with GUARD_ALLOW_PRIMARY_EDIT; got: $rc"
    fail=1
fi

# 12. Deny message names the escape hatch so the operator knows the recourse.
out=$(_run_hook "$WORKTREE" "$PRIMARY" "$PRIMARY/src/main.py")
if echo "$out" | grep -q "GUARD_ALLOW_PRIMARY_EDIT"; then
    echo "PASS: deny message names GUARD_ALLOW_PRIMARY_EDIT"
else
    echo "FAIL: deny message missing GUARD_ALLOW_PRIMARY_EDIT; got: $out"
    fail=1
fi

# 13. Allow cases exit 0 explicitly — silence alone no longer implies allowed
# now that the guard can deny (exit 2).
rc=$(_rc "$WORKTREE" "$PRIMARY" "$WORKTREE/src/main.py")
if [ "$rc" = "0" ]; then
    echo "PASS: worktree-rooted path exits 0"
else
    echo "FAIL: expected exit 0 for worktree-rooted path; got: $rc"
    fail=1
fi
rc=$(_rc "$WORKTREE" "$PRIMARY" "/tmp/unrelated/file.py")
if [ "$rc" = "0" ]; then
    echo "PASS: unrelated path exits 0"
else
    echo "FAIL: expected exit 0 for unrelated path; got: $rc"
    fail=1
fi

# 14. NotebookEdit whose notebook_path (NOT file_path) targets the primary
# checkout → deny (exit 2 + corrective message). The settings.json matcher
# covers NotebookEdit, so the guard must read notebook_path; a jq that reads
# only file_path returns empty here and silently allows the primary-checkout
# write (the exact bypass this case guards).
rc=$(_rc_notebook "$WORKTREE" "$PRIMARY" "$PRIMARY/nb.ipynb")
if [ "$rc" = "2" ]; then
    echo "PASS: denies NotebookEdit notebook_path into primary (exit 2)"
else
    echo "FAIL: expected exit 2 for NotebookEdit into primary; got: $rc"
    fail=1
fi
out=$(_run_hook_notebook "$WORKTREE" "$PRIMARY" "$PRIMARY/nb.ipynb")
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: NotebookEdit into primary emits corrective message"
else
    echo "FAIL: expected corrective message for NotebookEdit into primary; got: $out"
    fail=1
fi

# 15. NotebookEdit whose notebook_path is inside the worktree → allow (exit 0).
rc=$(_rc_notebook "$WORKTREE" "$PRIMARY" "$WORKTREE/nb.ipynb")
if [ "$rc" = "0" ]; then
    echo "PASS: allows NotebookEdit notebook_path inside worktree (exit 0)"
else
    echo "FAIL: expected exit 0 for NotebookEdit inside worktree; got: $rc"
    fail=1
fi

# 16. `..`-traversal evasion (ticket 0323, residual 1): a raw file_path that does
# NOT lexically begin with $PRIMARY but collapses into it via `..` must still be
# denied. Without realpath normalization the prefix match on the raw string
# passes (exit 0, silent bypass); `realpath -m` collapses the `..` — tolerating a
# not-yet-existing leaf — so the normalized path matches $PRIMARY and denies.
rc=$(_rc "$WORKTREE" "$PRIMARY" "/home/testuser/x/../repo/evil.py")
if [ "$rc" = "2" ]; then
    echo "PASS: denies dot-dot-traversal path that collapses into primary (exit 2)"
else
    echo "FAIL: expected exit 2 for dot-dot-traversal into primary; got: $rc"
    fail=1
fi
out=$(_run_hook "$WORKTREE" "$PRIMARY" "/home/testuser/x/../repo/evil.py")
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: dot-dot-traversal into primary emits corrective message"
else
    echo "FAIL: expected corrective message for dot-dot-traversal; got: $out"
    fail=1
fi

# 17. Symlink-through evasion (ticket 0323, residual 1): a file_path routed through
# a symlink that points at the primary root has a raw string that does NOT start
# with the real primary-root path, so the prefix match misses (silent bypass).
# `realpath -m` resolves the symlink in the existing dir components, exposing the
# primary root, and the guard denies. Real-git fixture (no env override), mirroring
# cases 8/9 so the identity predicate and root resolution run for real.
_case17_base=$(mktemp -d)
_case17_primary="$_case17_base/primary"
mkdir -p "$_case17_primary"
git -C "$_case17_primary" init -q
git -C "$_case17_primary" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
mkdir -p "$_case17_primary/.claude/worktrees"
git -C "$_case17_primary" worktree add -q "$_case17_primary/.claude/worktrees/t001"
# Symlink OUTSIDE the primary root pointing back at it; a path through it evades
# the raw-string prefix match against the real primary-root path.
ln -s "$_case17_primary" "$_case17_base/plink"
out=$( cd "$_case17_primary/.claude/worktrees/t001" \
       && printf '{"tool_name":"Write","tool_input":{"file_path":"%s/src/main.py","content":"x"}}' "$_case17_base/plink" \
       | bash "$HOOK" 2>&1 || true)
git -C "$_case17_primary" worktree remove --force "$_case17_primary/.claude/worktrees/t001" 2>/dev/null || true
rm -r "$_case17_base"
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: denies path routed through a symlink into primary (identity predicate)"
else
    echo "FAIL: expected deny for symlink-through into primary; got: $out"
    fail=1
fi

# 18. Cross-worktree deny (ticket 0342): two sibling harness worktrees under one
# primary — a session worktree `t-session` and a gaze review worktree
# `review-999`. A process INSIDE t-session that targets a file inside review-999
# must be DENIED. The guard has no `review-*` allowlist (0300 moved review
# worktrees under `.claude/worktrees/` for identity COVERAGE, not to whitelist
# the name); a path is allowed only when the acting worktree physically contains
# it. This is the exact scenario gaze phase 5 hits while `/simplify` is a direct
# invocation: the fork's cwd is a sibling worktree, so its Edit into review-999
# is denied. Case 19 is its silent-allow companion. Real-git fixture (cases
# 8/9/17 style) so identity resolution runs for real. Case 18 also guards
# against "fixing" 0342 by adding a review-* allowlist — that would flip it FAIL.
_case18_primary=$(mktemp -d)
git -C "$_case18_primary" init -q
git -C "$_case18_primary" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
mkdir -p "$_case18_primary/.claude/worktrees"
git -C "$_case18_primary" worktree add -q "$_case18_primary/.claude/worktrees/t-session"
git -C "$_case18_primary" worktree add -q "$_case18_primary/.claude/worktrees/review-999"
out=$( cd "$_case18_primary/.claude/worktrees/t-session" \
       && printf '{"tool_name":"Write","tool_input":{"file_path":"%s/.claude/worktrees/review-999/fix.py","content":"x"}}' "$_case18_primary" \
       | bash "$HOOK" 2>&1 || true)
if echo "$out" | grep -q "Worktree path guard"; then
    echo "PASS: denies Edit from one worktree into a sibling review-* worktree"
else
    echo "FAIL: expected deny for cross-worktree edit into review-999; got: $out"
    fail=1
fi

# 19. Silent-allow companion to case 18: a process INSIDE review-999 editing a
# file inside review-999 is allowed (exit 0, silent) — the acting worktree
# contains the target. Confirms the deny in case 18 is about worktree identity,
# not the `review-*` name.
rc=$( cd "$_case18_primary/.claude/worktrees/review-999" \
      && printf '{"tool_name":"Write","tool_input":{"file_path":"%s/.claude/worktrees/review-999/fix.py","content":"x"}}' "$_case18_primary" \
      | bash "$HOOK" >/dev/null 2>&1; echo $? )
if [ "$rc" = "0" ]; then
    echo "PASS: allows Edit inside the review-* worktree the process runs from (exit 0)"
else
    echo "FAIL: expected exit 0 editing inside review-999 from review-999; got: $rc"
    fail=1
fi
git -C "$_case18_primary" worktree remove --force "$_case18_primary/.claude/worktrees/t-session" 2>/dev/null || true
git -C "$_case18_primary" worktree remove --force "$_case18_primary/.claude/worktrees/review-999" 2>/dev/null || true
rm -rf "$_case18_primary"

exit $fail
