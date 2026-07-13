#!/usr/bin/env bash
# Tests for scripts/guard-enterworktree-parked-cwd.sh — the matcher-agnostic
# PreToolUse hook (wired for EnterWorktree and Skill) that denies (exit 2) when
# the session base cwd is parked in a git-ignored runtime directory, so the tool
# would target the wrong repo. See tickets 0267 (EnterWorktree) and 0306 (Skill).
#
# The guard is driven purely by the JSON payload's .cwd field against real
# directories, so the tests build a throwaway git repo in a temp dir.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/guard-enterworktree-parked-cwd.sh"
RULES="$HOME/.claude/rules/workflow.md"
fail=0

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# A repo with a tracked subdir and a git-ignored runtime dir.
REPO="$TMP/repo"
git init -q "$REPO"
mkdir -p "$REPO/src" "$REPO/projects/session-x"
echo "projects/" > "$REPO/.gitignore"
touch "$REPO/src/keep"
git -C "$REPO" add -A
git -C "$REPO" -c user.email=t@t -c user.name=t commit -qm init

# A plain non-repo directory.
NOREPO="$TMP/norepo"
mkdir -p "$NOREPO"

_rc() {
    local cwd="$1" tool="${2:-EnterWorktree}"
    printf '{"tool_name":%s,"tool_input":{},"cwd":%s}' \
        "$(printf '%s' "$tool" | jq -Rs .)" \
        "$(printf '%s' "$cwd" | jq -Rs .)" \
        | bash "$HOOK" >/dev/null 2>&1 && echo 0 || echo $?
}

_assert() {
    local expected="$1" label="$2" cwd="$3" tool="${4:-EnterWorktree}"
    local rc; rc=$(_rc "$cwd" "$tool")
    if [[ "$rc" == "$expected" ]]; then
        echo "PASS: $label (exit $rc)"
    else
        echo "FAIL: $label — expected exit $expected, got $rc (cwd: $cwd)"
        fail=1
    fi
}

# --- DENY: cwd parked in a git-ignored runtime dir --------------------------
_assert 2 "denies cwd in git-ignored dir"        "$REPO/projects"
_assert 2 "denies cwd deep in git-ignored dir"   "$REPO/projects/session-x"

# --- ALLOW -------------------------------------------------------------------
_assert 0 "allows cwd at repo root"              "$REPO"
_assert 0 "allows cwd in tracked subdir"         "$REPO/src"
_assert 0 "allows cwd outside any repo"          "$NOREPO"
_assert 0 "allows nonexistent cwd (fail-safe)"   "$TMP/does-not-exist"

# --- Nested repo inside an ignored runtime dir must still deny (ticket 0317) --
# A `git init` inside a git-ignored runtime dir makes `git rev-parse
# --show-toplevel` resolve to the nested repo itself: the toplevel self-match
# would pass and the deny would be bypassed. The guard walks up to the enclosing
# repo and re-probes, so a parked cwd stays denied even with a nested repo.
NESTED="$REPO/projects/session-x/scratch"
git init -q "$NESTED"
mkdir -p "$NESTED/tracked"
touch "$NESTED/tracked/keep"
git -C "$NESTED" add -A
git -C "$NESTED" -c user.email=t@t -c user.name=t commit -qm init

_assert 2 "denies nested-repo root in ignored dir"   "$NESTED"
_assert 2 "denies tracked subdir of nested repo"     "$NESTED/tracked"

# --- Registered linked worktree under a whitelist-ignore repo must ALLOW ------
# The harness's own mandated layout puts every session worktree at
# <repo>/.claude/worktrees/<name>. When the enclosing repo uses a whitelist-style
# `*` .gitignore (as the harness repo does), that path is check-ignored by the
# enclosing repo — but a `git worktree add` worktree is legitimate, not a parked
# scratch dir. A linked worktree has a .git FILE (a `gitdir:` pointer), unlike a
# nested `git init` (.git DIRECTORY), so the guard must exempt it from the
# enclosing-repo walk-up and allow it (ticket 0317 round-1 reroll).
WL="$TMP/whitelist-repo"
git init -q "$WL"
printf '*\n!/.gitignore\n!/src\n!/src/**\n' > "$WL/.gitignore"
mkdir -p "$WL/src"
touch "$WL/src/keep"
git -C "$WL" add -A
git -C "$WL" -c user.email=t@t -c user.name=t commit -qm init
# A real linked worktree at the harness-style path (check-ignored by the `*` rule).
git -C "$WL" -c user.email=t@t -c user.name=t \
    worktree add -q "$WL/.claude/worktrees/wt" -b wt-branch >/dev/null 2>&1

_assert 0 "allows registered linked worktree root"        "$WL/.claude/worktrees/wt"
_assert 0 "allows linked worktree root (Skill)"           "$WL/.claude/worktrees/wt"   "Skill"

# --- Skill invocations: the guard is matcher-agnostic (ticket 0306) ----------
# A cwd-dependent skill resolves its target repo from the same session base cwd,
# so a parked cwd must be denied and a repo-root cwd allowed for Skill too.
_assert 2 "denies Skill from git-ignored dir"    "$REPO/projects"        "Skill"
_assert 0 "allows Skill at repo root"            "$REPO"                 "Skill"
_assert 0 "allows Skill in tracked subdir"       "$REPO/src"             "Skill"
_assert 0 "allows Skill outside any repo"        "$NOREPO"               "Skill"

# --- Symlink traversal: cwd is realpath-normalized before the probes (0314) ---
# A path that reaches the repo through a symlink must resolve to its real
# location before the check-ignore probe. Otherwise check-ignore errors
# "outside repository", the guard falls through to allow, and a parked runtime
# directory addressed via a symlink bypasses the deny (found by the PR #545 panel).
LINK_PARKED="$TMP/link-parked"
ln -s "$REPO/projects/session-x" "$LINK_PARKED"
LINK_ROOT="$TMP/link-root"
ln -s "$REPO" "$LINK_ROOT"

_assert 2 "denies symlinked parked cwd"              "$LINK_PARKED"
_assert 2 "denies symlinked parked cwd (Skill)"      "$LINK_PARKED"          "Skill"
# A symlinked ancestor *component* (real leaf under a symlinked root) must also
# normalize before the probes.
_assert 2 "denies parked cwd via symlinked ancestor" "$LINK_ROOT/projects/session-x"
_assert 0 "allows symlinked repo-root cwd"           "$LINK_ROOT"
_assert 0 "allows symlinked repo-root cwd (Skill)"   "$LINK_ROOT"            "Skill"

# --- Payload without .cwd → fail-safe allow ---------------------------------
rc=$(printf '{"tool_name":"EnterWorktree","tool_input":{}}' \
        | bash "$HOOK" >/dev/null 2>&1; echo $?)
if [[ "$rc" == "0" ]]; then
    echo "PASS: allows payload with no .cwd (fail-safe)"
else
    echo "FAIL: expected allow for payload with no .cwd; got exit $rc"
    fail=1
fi

# --- Deny message names the resolved repo and the fallback recipe -----------
err=$(printf '{"tool_name":"EnterWorktree","tool_input":{},"cwd":%s}' \
        "$(printf '%s' "$REPO/projects" | jq -Rs .)" \
        | bash "$HOOK" 2>&1 1>/dev/null) || true
for needle in "worktree add" "show-toplevel" "0267"; do
    if grep -qF "$needle" <<< "$err"; then
        echo "PASS: deny message mentions '$needle'"
    else
        echo "FAIL: deny message missing '$needle'"
        fail=1
    fi
done

# --- Deny message names the blocked tool, not a hard-coded EnterWorktree ------
skill_err=$(printf '{"tool_name":"Skill","tool_input":{},"cwd":%s}' \
        "$(printf '%s' "$REPO/projects" | jq -Rs .)" \
        | bash "$HOOK" 2>&1 1>/dev/null) || true
if grep -qF "Skill resolves its target repo" <<< "$skill_err"; then
    echo "PASS: Skill deny message names the Skill tool"
else
    echo "FAIL: Skill deny message does not name the blocked tool"
    fail=1
fi

# --- jq missing → fail-open --------------------------------------------------
_tmpbin=$(mktemp -d)
ln -s "$(type -P cat)" "$_tmpbin/cat"
ln -s "$(type -P git)" "$_tmpbin/git"
_real_bash="$(type -P bash)"
rc=$(printf '{"tool_name":"EnterWorktree","tool_input":{},"cwd":"%s"}' "$REPO/projects" \
        | env PATH="$_tmpbin" "$_real_bash" "$HOOK" >/dev/null 2>&1; echo $?)
rm -rf "$_tmpbin"
if [[ "$rc" == "0" ]]; then
    echo "PASS: fails open (exit 0) when jq is missing"
else
    echo "FAIL: expected fail-open (exit 0) without jq; got exit $rc"
    fail=1
fi

# --- Doc ratchet: rules/workflow.md documents the parked-cwd trap ------------
# Use the checked-out copy when running from a branch/worktree, so the ratchet
# tests THIS revision, not whatever the primary checkout has.
[ -f "$PWD/rules/workflow.md" ] && RULES="$PWD/rules/workflow.md"
for needle in "parked" "show-toplevel" "worktree add"; do
    if grep -qF "$needle" "$RULES"; then
        echo "PASS: workflow.md documents '$needle'"
    else
        echo "FAIL: workflow.md missing '$needle' (parked-cwd trap undocumented)"
        fail=1
    fi
done

# --- Wiring ratchet: settings.json routes EnterWorktree through the guard ----
# The matcher may name the tool alone or in a pipe-alternation ("A|B"), so the
# ratchet matches the tool name as a full alternative, not by equality.
if jq -e '.hooks.PreToolUse[] | select(.matcher | test("(^|\\|)EnterWorktree(\\||$)"))
          | .hooks[].command | test("guard-enterworktree-parked-cwd")' \
        settings.json >/dev/null 2>&1; then
    echo "PASS: settings.json wires the EnterWorktree guard"
else
    echo "FAIL: settings.json has no EnterWorktree PreToolUse hook for the guard"
    fail=1
fi

# --- Wiring ratchet: settings.json routes Skill through the guard (0306) ------
if jq -e '.hooks.PreToolUse[] | select(.matcher | test("(^|\\|)Skill(\\||$)"))
          | .hooks[].command | test("guard-enterworktree-parked-cwd")' \
        settings.json >/dev/null 2>&1; then
    echo "PASS: settings.json wires the Skill guard"
else
    echo "FAIL: settings.json has no Skill PreToolUse hook for the guard"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: guard-enterworktree-parked-cwd denies parked-cwd EnterWorktree calls"
