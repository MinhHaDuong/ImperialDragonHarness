#!/usr/bin/env bash
# Guard (ticket 0348): BASH_ENV/hook scripts must be tested via a real hermetic
# subprocess, never sourced into the test's own shell.
#
# scripts/bash-env.sh is loaded by a FRESH non-interactive bash on every
# subprocess (via BASH_ENV). Its real behaviour — re-entry, ambient-env leakage
# across the env boundary, export-name collisions with the caller — only appears
# in that invocation path. Three security defects (a BASH_ENV re-entry fork
# bomb, an ambient-env leak, a guard-name forgery) passed a source-in-shell unit
# suite and were caught only by runtime review (PRs #599/#604). This guard makes
# the "test via a real subprocess" discipline mechanical.
#
# For every tests/test_bash_env_*.sh (except this file) it asserts:
#   A. the test invokes bash-env.sh inside a `bash -c` subprocess;
#   B. that subprocess runs under a controlled HOME (`HOME=` or `env -i`), so an
#      inherited variable or the live $HOME cannot mask a bug;
#   C. the test never sources/dots bash-env.sh (by literal path or "$SCRIPT")
#      into its OWN shell — the anti-pattern the rule forbids.
# See rules/coding-bash.md § "BASH_ENV / hook scripts".
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$(basename "${BASH_SOURCE[0]}")"

fail=0
checked=0
for f in "$TESTS_DIR"/test_bash_env_*.sh; do
    b="$(basename "$f")"
    [ "$b" = "$SELF" ] && continue
    checked=$((checked + 1))

    if ! grep -qE 'bash -c' "$f"; then
        echo "FAIL: $b — does not invoke bash-env.sh in a 'bash -c' subprocess" >&2
        fail=$((fail + 1))
        continue
    fi
    if ! grep -qE '(HOME=|env -i)' "$f"; then
        echo "FAIL: $b — subprocess is not run under a controlled HOME (needs 'HOME=' or 'env -i')" >&2
        fail=$((fail + 1))
        continue
    fi
    if grep -qE '^[[:space:]]*(source|\.)[[:space:]]+.*(bash-env\.sh|SCRIPT)' "$f"; then
        echo "FAIL: $b — sources bash-env.sh into the test's own shell (must run it in a subprocess)" >&2
        fail=$((fail + 1))
        continue
    fi
    echo "PASS: $b"
done

if [ "$checked" -eq 0 ]; then
    echo "FAIL: no tests/test_bash_env_*.sh found — guard has nothing to protect" >&2
    exit 1
fi
if [ "$fail" -ne 0 ]; then
    echo "GUARD FAILED: $fail of $checked bash-env test(s) do not use the hermetic-subprocess pattern" >&2
    exit 1
fi
echo "OK: all $checked bash-env test(s) use the hermetic-subprocess pattern"
