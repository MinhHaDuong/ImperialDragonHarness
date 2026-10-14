#!/bin/bash
# Positive control: does an info/exclude'd .tmp/ show in porcelain status, and does worktree remove delete it without --force?
set -u
D=$(mktemp -d /tmp/claude-1000/-home-haduong--agents/d331a70c-1c54-49b8-b99e-07b43275c08a/scratchpad/1095/probe.XXXX)
cd "$D"
git init -q main && cd main && git commit -q --allow-empty -m init
git worktree add -q ../wt -b wt
echo '.tmp/' >> "$(git rev-parse --git-common-dir)/info/exclude"
mkdir ../wt/.tmp && echo evidence > ../wt/.tmp/keep.txt
echo "control: untracked file visible?"; echo x > ../wt/untracked.txt
git -C ../wt status --porcelain --untracked-files=all
rm ../wt/untracked.txt
echo "probe: excluded .tmp visible? (empty = invisible)"
git -C ../wt status --porcelain --untracked-files=all
echo "with --ignored:"; git -C ../wt status --porcelain --ignored
echo "worktree remove without --force:"; git worktree remove ../wt; echo "exit=$?"
ls -la ../wt/.tmp 2>&1 | head -3
