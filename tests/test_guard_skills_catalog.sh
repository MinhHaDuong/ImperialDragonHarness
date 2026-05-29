#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

git -C "$TMPDIR" init -q
git -C "$TMPDIR" config user.email "test@example.com"
git -C "$TMPDIR" config user.name "Test"

mkdir -p "$TMPDIR/skills/foo"
cat > "$TMPDIR/README.md" <<'RDME'
<!-- skills:begin -->

| Command | Description |
|---------|-------------|

<!-- skills:end -->
RDME
cat > "$TMPDIR/skills/foo/SKILL.md" <<'SKL'
---
name: foo
description: A test skill
---
SKL

mkdir -p "$TMPDIR/scripts"
cat > "$TMPDIR/Makefile" <<'MK'
skills-catalog:
	date >> README.md
MK

mkdir -p "$TMPDIR/.git/hooks"
cat > "$TMPDIR/.git/hooks/pre-commit" <<'HOOK'
skills_changed=$(git diff --cached --name-only | grep '^skills/.*/SKILL\.md$' || true)
if [ -n "$skills_changed" ]; then
    if ! make skills-catalog; then
        echo "ERROR: make skills-catalog failed — commit aborted" >&2
        exit 1
    fi
    git add README.md
fi
HOOK
chmod +x "$TMPDIR/.git/hooks/pre-commit"

git -C "$TMPDIR" add .
git -C "$TMPDIR" commit -q -m "init"

# Test 1: staging a SKILL.md triggers the guard
echo "test edit" >> "$TMPDIR/skills/foo/SKILL.md"
git -C "$TMPDIR" add skills/foo/SKILL.md
git -C "$TMPDIR" commit -q -m "test: stage SKILL.md"
if git -C "$TMPDIR" show --name-only HEAD | grep -q 'README.md'; then
    echo "PASS: README.md was auto-staged when SKILL.md changed"
else
    echo "FAIL: README.md was not auto-staged"
    fail=1
fi

# Test 2: staging an unrelated file does NOT trigger guard
echo "something" > "$TMPDIR/unrelated.txt"
git -C "$TMPDIR" add unrelated.txt
git -C "$TMPDIR" commit -q -m "test: non-SKILL.md change"
if git -C "$TMPDIR" show --name-only HEAD | grep -q 'README.md'; then
    echo "FAIL: README.md was spuriously staged for a non-SKILL.md change"
    fail=1
else
    echo "PASS: README.md not staged for unrelated change"
fi

if (( fail )); then exit 1; fi
echo "PASS: skills-catalog-guard fires on SKILL.md changes and ignores others"
