#!/usr/bin/env bash
# Run the zotero skill's probe-url selftest (14 offline assertions, no network)
# as a harness CI suite. Auto-discovered by tests/test_bash_suites.py.
set -euo pipefail
cd "$(dirname "$0")/.."
# `env -i` on the exec'd selftest (ticket 0875): a plain `bash FILE` child
# inherits BASH_ENV and re-runs the project .env loader inside the very
# selftest whose offline assertions are under test. The selftest is pure
# Python-on-fixtures — HOME and PATH are its whole contract.
exec env -i HOME="$HOME" PATH="$PATH" bash skills/zotero/scripts/selftest.sh
