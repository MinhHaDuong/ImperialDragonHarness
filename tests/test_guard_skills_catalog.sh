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
cp "$(git rev-parse --show-toplevel)/hooks/pre-commit" "$TMPDIR/.git/hooks/pre-commit"
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

# Test 3: pre-commit hook must not carry the stale 'Run make build first' text.
# IDH vendors the erg binary at tickets/erg — there is no `make build` target.
# Guards against erg install --hooks reintroducing the upstream template string
# (tracked upstream in ticket 0231). RED against the pre-0230 hook text.
HOOK="$(git rev-parse --show-toplevel)/hooks/pre-commit"
if grep -q "Run 'make build' first" "$HOOK"; then
    echo "FAIL: hooks/pre-commit still says \"Run 'make build' first\" (no make build in IDH; see ticket 0231)"
    fail=1
else
    echo "PASS: hooks/pre-commit free of stale 'make build' error text"
fi

if (( fail )); then exit 1; fi
echo "PASS: skills-catalog-guard fires on SKILL.md changes and ignores others"
