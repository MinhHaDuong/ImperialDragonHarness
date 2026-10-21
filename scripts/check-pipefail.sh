#!/usr/bin/env bash
# Guard: every hook script carries `set -euo pipefail`.
# Usage: check-pipefail.sh [file ...]   (default: scripts/*.sh)
# Moved out of the CI workflow's inline step (ticket 1156) so the forge job and
# a merge-gate declaration can run one definition, not two copies.
# Sourced helpers, which must not change the caller's shell options, are exempt.
set -euo pipefail

if [ $# -eq 0 ]; then
    set -- scripts/*.sh
fi

for f in "$@"; do
    [ -r "$f" ] && [ -f "$f" ] || { echo "FAIL: cannot read $f"; exit 2; }
done

missing=$(grep -L 'set -euo pipefail' "$@" | grep -Ev 'shell-init\.sh|bashrc-loader\.sh|bash-env\.sh' || true)
if [ -n "$missing" ]; then
    echo "FAIL: missing set -euo pipefail in:"
    echo "$missing"
    exit 1
fi
echo "OK: all hook scripts have set -euo pipefail"
