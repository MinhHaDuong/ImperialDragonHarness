#!/usr/bin/env bash
# Tests for scripts/guard-enterworktree-parked-cwd.sh — the PreToolUse
# EnterWorktree hook that denies (exit 2) when the session base cwd is parked
# in a git-ignored runtime directory, so EnterWorktree would create the
# worktree in the wrong repo. See ticket 0267.
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

# --- Skill invocations: the guard is matcher-agnostic (ticket 0306) ----------
# A cwd-dependent skill resolves its target repo from the same session base cwd,
# so a parked cwd must be denied and a repo-root cwd allowed for Skill too.
_assert 2 "denies Skill from git-ignored dir"    "$REPO/projects"        "Skill"
_assert 0 "allows Skill at repo root"            "$REPO"                 "Skill"
_assert 0 "allows Skill outside any repo"        "$NOREPO"               "Skill"

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
if jq -e '.hooks.PreToolUse[] | select(.matcher == "EnterWorktree")
          | .hooks[].command | test("guard-enterworktree-parked-cwd")' \
        settings.json >/dev/null 2>&1; then
    echo "PASS: settings.json wires the EnterWorktree guard"
else
    echo "FAIL: settings.json has no EnterWorktree PreToolUse hook for the guard"
    fail=1
fi

# --- Wiring ratchet: settings.json routes Skill through the guard (0306) ------
if jq -e '.hooks.PreToolUse[] | select(.matcher == "Skill")
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
