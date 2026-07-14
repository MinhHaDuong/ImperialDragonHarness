#!/bin/bash
set -euo pipefail
# PreToolUse hook: deny (exit 2 + stderr) when Write/Edit/NotebookEdit targets
# the main repo path during a worktree session — the worktree-path trap
# (rules/workflow.md § Worktree paths). Ticket 0171 shipped this as an advisory
# (exit 0); ticket 0318 hardened it to a blocking deny after prose warnings
# failed to stop 7/11 execute agents in one raid.
# See tickets 0171 and 0318.

input=$(cat)

command -v jq &>/dev/null || exit 0

# NotebookEdit carries its target in notebook_path, Write/Edit in file_path. A
# payload has only one, so read either; without this the guard silently exits 0
# on every NotebookEdit despite the settings.json matcher covering it.
file_path=$(echo "$input" | jq -r '.tool_input.notebook_path // .tool_input.file_path // empty' 2>/dev/null || true)
[ -z "$file_path" ] && exit 0
hook_cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)

# Identity predicate (ticket 0308): a genuine harness worktree, not merely a
# directory carrying a `.git` gitdir: file (a submodule or an ad-hoc worktree
# would satisfy the old `[ -f .git ] && grep gitdir:` check and trip a spurious
# advisory). Mirrors `in_worktree()` in skills/merge/erg-pr-merge (0301) and
# scripts/guard-worktree-identity.sh: the cwd must sit under
# `.claude/worktrees/<name>` AND `git rev-parse --show-toplevel` must resolve to
# a tree whose basename is that `<name>` and is not the primary root itself.
# Ticket 0302 decided to keep this copy inline rather than extract a shared
# `scripts/lib/worktree-identity.sh`: the integrity guards read hook-JSON `.cwd`
# through `git -C` and are fail-closed, so no one helper fits all sites without
# changing an input model or a failure contract, and sourcing a lib into this
# fail-open hook would flip its semantics on a missing file. This copy and the
# one in `skills/merge/erg-pr-merge` are held in lockstep by
# tests/test_worktree_identity_predicate_inline.py instead.
_in_worktree() {
    local cwd top name prefix
    cwd=$(pwd -P)
    prefix=${cwd%%/.claude/worktrees/*}   # enclosing path before the marker
    name=${cwd#*/.claude/worktrees/}      # <name>[/subdir...]
    name=${name%%/*}
    [ -n "$name" ] || return 1
    top=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    [ -n "$top" ] || return 1
    [ "$(basename "$top")" = "$name" ] || return 1
    [ "$top" != "$prefix" ] || return 1
    return 0
}

# Allow env-var overrides for testing without a real git repo
if [ -n "${_GUARD_WORKTREE_ROOT:-}" ] && [ -n "${_GUARD_PRIMARY_ROOT:-}" ]; then
    worktree_root="$_GUARD_WORKTREE_ROOT"
    primary_root="$_GUARD_PRIMARY_ROOT"
elif _in_worktree; then
    worktree_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
    git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null) || exit 0
    primary_root=$(dirname "$git_common_dir")
else
    exit 0
fi

[ "$worktree_root" = "$primary_root" ] && exit 0

# Resolve relative file_path against the PreToolUse JSON's .cwd (the cwd the
# tool will run from), not the hook's own cwd. Fall back to $(pwd) when .cwd
# is absent so older runners and tests that don't supply it still work.
if [ "${file_path#/}" = "$file_path" ]; then
    if [ -n "$hook_cwd" ]; then
        file_path="$hook_cwd/$file_path"
    else
        file_path="$(pwd)/$file_path"
    fi
fi

# Normalize before the prefix match (ticket 0323, residual 1): a raw path with
# `..` traversal or through a symlinked directory does not lexically begin with
# $primary_root and would slip past the string-prefix `case` below. `realpath -m`
# collapses `..` and resolves symlinks in the existing dir components while
# tolerating a not-yet-existing leaf (--canonicalize-missing), which is correct
# at PreToolUse time — the file being written need not exist yet. Fall back to
# the raw path if realpath is unavailable. primary_root/worktree_root are left
# as-is: git rev-parse --show-toplevel already canonicalizes them, and they are
# opaque literals under the _GUARD_*_ROOT test override.
if command -v realpath &>/dev/null; then
    file_path=$(realpath -m -- "$file_path" 2>/dev/null || echo "$file_path")
fi

case "$file_path" in
    "$primary_root"/*)
        case "$file_path" in
            "$worktree_root"/*)
                exit 0  # already inside the worktree
                ;;
        esac
        rel="${file_path#$primary_root/}"
        # projects/*/memory/** is tracked via the primary .gitignore whitelist by
        # design, and skills/memory tells every session to write it directly by
        # absolute path — so a primary-checkout write there is intended, not the
        # trap. Scoped narrowly (NOT a blanket projects/* exemption); for a
        # non-harness project the pattern never matches, so it is a no-op.
        case "$rel" in
            projects/*/memory/*) exit 0 ;;
        esac
        # Escape hatch: a human pre-authorizes intentional primary edits by
        # exporting GUARD_ALLOW_PRIMARY_EDIT in the shell/systemd environment
        # BEFORE session start. The hook is spawned by the CLI, not a Bash-tool
        # subshell, so an agent cannot set it mid-turn.
        #
        # Provenance is enforced upstream (ticket 0323, residual 2): this hook
        # runs as a bash subprocess with BASH_ENV=scripts/bash-env.sh, which
        # sources a project `.env` under `set -a`. Without a guard an agent could
        # drop a `.env` in its own worktree setting GUARD_ALLOW_PRIMARY_EDIT=1
        # and have it auto-exported into this env before the check below —
        # self-service bypass. bash-env.sh now snapshots this one variable and
        # restores-or-unsets it around the `.env` sourcing, so only a value
        # present in the launch environment survives. See scripts/bash-env.sh.
        if [ -n "${GUARD_ALLOW_PRIMARY_EDIT:-}" ]; then
            exit 0
        fi
        echo "BLOCKED: Worktree path guard: '$rel' resolves to the main repo, not the worktree." >&2
        echo "Did you mean: $worktree_root/$rel" >&2
        echo "For an intentional primary-checkout edit, export GUARD_ALLOW_PRIMARY_EDIT before starting the session." >&2
        exit 2
        ;;
esac

exit 0
