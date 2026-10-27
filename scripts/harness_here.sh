#!/usr/bin/env bash
# Exit 0 when the current directory is inside the harness repository (its
# checkout or any of its worktrees), else print one line on stderr and exit 1.
# The harness doctor runs it first and stops on non-zero.
# Usage: harness_here.sh
set -euo pipefail

harness=$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
want=$(git -C "$harness" rev-parse --path-format=absolute --git-common-dir)
have=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)

if [ -z "$have" ] || [ "$have" != "$want" ]; then
    echo "harness-doctor runs only inside the harness repository ($harness); here is $(pwd -P)." >&2
    exit 1
fi
