#!/usr/bin/env bash
# Tests for scripts/lint-on-edit.sh — the PostToolUse hook that runs ruff on
# edited Python files. Policy (ticket 0212, building on 0201/PR #275): the repo
# has NO repo-wide formatter, so the hook must LINT but never `ruff format` —
# otherwise it silently reinstates the per-PR formatting churn 0201 reverted.
set -euo pipefail

cd "$(dirname "$0")/.."
HOOK="$PWD/scripts/lint-on-edit.sh"
fail=0

# --- static ratchet: the hook source must not invoke `ruff format` -----------
# Strip comment lines first so an explanatory comment mentioning `ruff format`
# is not mistaken for an actual invocation.
if grep -vE '^[[:space:]]*#' "$HOOK" | grep -qE 'ruff format'; then
    echo "FAIL: scripts/lint-on-edit.sh invokes 'ruff format' — reinstates the"
    echo "      formatting churn ticket 0201 reverted (no repo-wide formatter)."
    fail=1
else
    echo "PASS: hook does not invoke 'ruff format'"
fi

# --- static ratchet: lint is retained ----------------------------------------
if grep -qE 'ruff check' "$HOOK"; then
    echo "PASS: hook still runs 'ruff check' (lint retained)"
else
    echo "FAIL: hook no longer runs 'ruff check' — lint was dropped, not just format."
    fail=1
fi

# --- behavioral: running the hook must not reformat a lint-clean file ---------
# `x = {'a':1}` is untouched by `ruff check --fix` (quote/spacing are not in
# ruff's default lint select) but WOULD be rewritten to `x = {"a": 1}` by
# `ruff format`. So a byte-identical file after the hook proves format is off.
# Gate on the same capability the hook uses (uv-run ruff OR bare ruff), so the
# check still runs in a uv-only environment where bare `ruff` isn't on PATH.
if command -v uv &>/dev/null || command -v ruff &>/dev/null; then
    probe=$(mktemp --suffix=.py)
    printf "x = {'a':1}\n" > "$probe"
    before=$(cat "$probe")
    printf '{"tool_name":"Edit","tool_input":{"file_path":%s}}' \
        "$(printf '%s' "$probe" | jq -Rs .)" \
        | bash "$HOOK" >/dev/null 2>&1 || true
    after=$(cat "$probe")
    rm -f "$probe"
    if [[ "$before" == "$after" ]]; then
        echo "PASS: hook leaves a format-only deviation untouched"
    else
        echo "FAIL: hook reformatted the file (before: [$before] after: [$after])"
        fail=1
    fi
else
    echo "SKIP: ruff not installed — behavioral reformat check not run"
fi

if (( fail )); then
    exit 1
fi
echo "PASS: lint-on-edit lints without formatting"
