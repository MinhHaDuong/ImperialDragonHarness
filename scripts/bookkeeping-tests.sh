#!/usr/bin/env bash
# The bookkeeping tier's test check (ticket 1221; policy: skills/merge/SKILL.md
# § Gating tiers). A bookkeeping-only merge (tickets, STATE.md, memory) skips
# the full suite, but must not turn main red: run every test that reads the
# repository's own bookkeeping data, e.g. the STATE.md line cap. The set is
# selected at run time from the source (a test naming `ROOT / "STATE.md"`,
# `REPO / "memory"` or `ROOT / "tickets"`), so a new such test is not left out
# by a stale list. Run from the repository root; no reader found is an error,
# never a pass.
set -euo pipefail

pattern='(ROOT|REPO)[[:space:]]*/[[:space:]]*"(STATE\.md|memory|tickets)"'
mapfile -t files < <(grep -lE "$pattern" tests/test_*.py 2>/dev/null || true)
if [ "${#files[@]}" -eq 0 ]; then
    echo "bookkeeping-tests: no test reads tickets/, memory/ or STATE.md; refusing an empty run" >&2
    exit 2
fi

# Interpreter as the Makefile's RUN: bare inside an activated env or without uv.
if [ -z "${VIRTUAL_ENV:-}" ] && command -v uv >/dev/null 2>&1; then
    run=(uv run --frozen python3)
else
    run=(python3)
fi
printf 'bookkeeping-tests: %s\n' "${files[@]}"
"${run[@]}" -m pytest -q -p no:cacheprovider "${files[@]}"
