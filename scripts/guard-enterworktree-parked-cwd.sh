#!/bin/bash
set -euo pipefail
# PreToolUse hook: deny EnterWorktree — and any cwd-dependent Skill invocation
# (matcher "Skill") — when the session base cwd is parked in a git-ignored
# runtime directory (e.g. ~/.claude/projects, ~/.claude/jobs). Both resolve
# their target repo from the session base cwd, so a parked cwd silently targets
# the nearest enclosing repo, not the intended project. The guard reads only the
# .cwd field, so it is matcher-agnostic — the same script serves both matchers.
# Exit 0 = allow, Exit 2 = deny. See tickets 0267 (EnterWorktree) and 0306 (Skill).
#
# A `cd` inside a Bash call never moves the session base cwd — it resets after
# every call — so the only reliable signal is the .cwd field of the hook JSON.

# find_enclosing_ignored_toplevel <inner_toplevel>
# Walk up from the parent of <inner_toplevel>. For each enclosing git repo, test
# whether <inner_toplevel> sits under a git-ignored path of that repo; on the
# first such match echo the enclosing repo's toplevel and return 0. Return 1 if
# no enclosing repo ignores it before the walk reaches / or leaves every repo.
# Why the walk-up: a `git init` inside a git-ignored runtime dir makes
# `git rev-parse --show-toplevel` resolve to the nested scratch repo, so the
# self-match and same-repo check-ignore in the main flow both pass and the
# parked-cwd deny is bypassed (ticket 0317, flagged by the PR #548 panel). Nested
# scratch repos in runtime dirs must not defeat the deny; the guard stays
# deny-only defense-in-depth. A non-ignored enclosing repo (a legit nested
# checkout) is walked past, not treated as a match.
find_enclosing_ignored_toplevel() {
    local inner="$1" dir outer parent
    dir=$(dirname "$inner")
    while :; do
        outer=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || return 1
        if git -C "$outer" check-ignore -q "$inner" 2>/dev/null; then
            printf '%s\n' "$outer"
            return 0
        fi
        parent=$(dirname "$outer")
        [ "$parent" = "$outer" ] && return 1   # reached / — fixed point
        dir="$parent"
    done
}

input=$(cat)

command -v jq &>/dev/null || exit 0
command -v git &>/dev/null || exit 0

cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
[ -z "$cwd" ] && exit 0
[ -d "$cwd" ] || exit 0

# Normalize away symlinks before the repo-membership and check-ignore probes.
# A path that reaches the repo through a symlink otherwise makes
# `git check-ignore "$cwd"` error "outside repository", which the guard treats
# as allow — letting a parked runtime dir addressed via a symlink bypass the
# deny (ticket 0314). Fail open if resolution fails (e.g. a race removed the
# dir): a normalization failure must never flip an allow into a deny.
cwd=$(cd "$cwd" 2>/dev/null && pwd -P) || exit 0

# Not inside a git repo: the tool fails on its own (or hook-delegated
# VCS-agnostic mode handles it) — nothing for this guard to judge.
toplevel=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0

# Nested-repo escape (ticket 0317): if the resolved toplevel is itself parked in
# a git-ignored path of an enclosing repo, the cwd sits behind a nested scratch
# repo inside a runtime dir — the self-match and same-repo check-ignore below
# would both pass and bypass the deny. Deny, reporting the real enclosing project.
if enclosing=$(find_enclosing_ignored_toplevel "$toplevel"); then
    toplevel="$enclosing"
else
    # At the repo root, or in a tracked subdirectory: repo resolution is correct.
    [ "$cwd" = "$toplevel" ] && exit 0
    git -C "$cwd" check-ignore -q "$cwd" 2>/dev/null || exit 0
fi

# Parked cwd: a git-ignored runtime directory inside some repo. The tool would
# target that repo, which is almost never the intended project.
# The blocked tool, for an accurate message (EnterWorktree vs Skill, …) —
# extracted only on this rare deny path, keeping the hot allow path to one jq.
tool=$(echo "$input" | jq -r '.tool_name // "This tool"' 2>/dev/null || echo "This tool")
[ -z "$tool" ] && tool="This tool"

cat >&2 <<EOF
Blocked: the session base cwd is parked in a git-ignored runtime directory:
  cwd:  $cwd
  repo: $toplevel
$tool resolves its target repo from the session base cwd, so it would act on
'$toplevel' — likely not the intended project. A 'cd' in a Bash call does not
move the base cwd (it resets after every call).

If '$toplevel' IS the intended repo, invoke $tool from its root instead.
Otherwise re-launch the session (or EnterWorktree) with its base cwd at the
correct repo, or fall back to manual isolation:
  git -C <project> worktree add <project>/.claude/worktrees/<name> -b <branch>
then drive all work with absolute paths and 'git -C'. After any EnterWorktree,
verify ownership: basename "\$(git rev-parse --show-toplevel)" must match the
expected worktree/project name. See tickets 0267 and 0306.
EOF
exit 2
