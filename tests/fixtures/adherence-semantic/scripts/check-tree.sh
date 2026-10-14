#!/usr/bin/env bash
set -euo pipefail
if [ -f .git ]; then
    printf '%s\n' 'Git worktree'
fi
