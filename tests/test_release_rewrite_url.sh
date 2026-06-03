#!/usr/bin/env bash
# Tests for skills/release/rewrite-download-url — rewrites the tag-like
# segment inside raw-download / release URLs to a new release tag.
#
# Exit-code contract (the subtle part):
#   - exit code keys off "a tag-bearing download URL was FOUND", not
#     "the file bytes changed". So a second run with the same tag is a
#     content no-op but still exits 0 (the URL still matches).
#   - zero matching URLs → exit non-zero.
set -euo pipefail

cd "$(dirname "$0")/.."
HELPER="$PWD/skills/release/rewrite-download-url"
fail=0

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# (a) single download URL pinned to an old date tag → rewritten to new tag.
f_a="$TMPDIR/single.md"
cat > "$f_a" <<'MD'
# Install

    curl -fsSL https://example.com/repo/raw/2026-05-30/install.sh | sh
MD
if bash "$HELPER" "$f_a" 2026-06-03 >/dev/null 2>&1; then
    if grep -q '/raw/2026-06-03/' "$f_a" && ! grep -q '2026-05-30' "$f_a"; then
        echo "PASS: (a) single URL rewritten to new tag, old tag gone"
    else
        echo "FAIL: (a) URL not rewritten correctly"; cat "$f_a"; fail=1
    fi
else
    echo "FAIL: (a) helper exited non-zero on a matching URL"; fail=1
fi

# (b) two URLs in one file → both rewritten.
f_b="$TMPDIR/double.md"
cat > "$f_b" <<'MD'
Download script: https://example.com/repo/raw/2026-05-30/install.sh
Download binary: https://example.com/repo/download/2026-05-30/erg
MD
if bash "$HELPER" "$f_b" 2026-06-03 >/dev/null 2>&1; then
    n_new=$(grep -c '2026-06-03' "$f_b")
    if [[ "$n_new" -eq 2 ]] && ! grep -q '2026-05-30' "$f_b"; then
        echo "PASS: (b) both URLs rewritten"
    else
        echo "FAIL: (b) expected 2 rewrites, found $n_new new / old remaining"; cat "$f_b"; fail=1
    fi
else
    echo "FAIL: (b) helper exited non-zero with two matching URLs"; fail=1
fi

# (c) no matching download URL → exit non-zero AND print a diagnostic.
# The diagnostic assertion guards against an errexit-on-grep regression where
# the script aborts before the explicit zero-count branch, silently dropping
# the "no tag-bearing download URL found" message.
f_c="$TMPDIR/nomatch.md"
cat > "$f_c" <<'MD'
# README

No download URL here, just prose and a plain link https://example.com/repo.
MD
c_err="$TMPDIR/nomatch.err"
if bash "$HELPER" "$f_c" 2026-06-03 >/dev/null 2>"$c_err"; then
    echo "FAIL: (c) helper exited zero on a file with no matching URL"; fail=1
elif grep -qi 'no tag-bearing download URL' "$c_err"; then
    echo "PASS: (c) helper exits non-zero and prints a diagnostic when no URL matches"
else
    echo "FAIL: (c) helper exited non-zero but printed no diagnostic"; cat "$c_err"; fail=1
fi

# (d) idempotence — second run with the same tag exits 0, file unchanged.
f_d="$TMPDIR/idem.md"
cat > "$f_d" <<'MD'
    curl -fsSL https://example.com/repo/raw/2026-06-03/install.sh | sh
MD
before=$(cat "$f_d")
if bash "$HELPER" "$f_d" 2026-06-03 >/dev/null 2>&1; then
    after=$(cat "$f_d")
    if [[ "$before" == "$after" ]]; then
        echo "PASS: (d) idempotent re-run exits 0 and leaves file unchanged"
    else
        echo "FAIL: (d) file changed on idempotent re-run"; diff <(echo "$before") <(echo "$after"); fail=1
    fi
else
    echo "FAIL: (d) helper exited non-zero on a URL already at the target tag"; fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: rewrite-download-url handles single, double, no-match, and idempotent cases"
