#!/usr/bin/env bash
set -eu
if [ -f .git ]; then
    printf '%s\n' 'Git worktree'
fi
