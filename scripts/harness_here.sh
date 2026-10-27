#!/usr/bin/env bash
# Exit 0 when the current directory is inside the harness repository (its
# checkout or any of its worktrees), else print one line on stderr and exit 1.
# The harness doctor runs it first and stops on non-zero.
# Usage: harness_here.sh
set -euo pipefail

# An exported repository override would make git answer for that repository
# instead of the current directory.
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR

common_dir() {  # physical path of the git common dir of $1, or nothing
    local d
    d=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 0
    (cd "$d" && pwd -P)
}

harness=$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
want=$(common_dir "$harness")
have=$(common_dir .)

if [ -z "$want" ]; then
    echo "harness-doctor cannot read the harness repository at $harness." >&2
    exit 1
fi
if [ "$have" != "$want" ]; then
    echo "harness-doctor runs only inside the harness repository ($harness); here is $(pwd -P)." >&2
    exit 1
fi
