#!/usr/bin/env bash
# Run the index-source probe-url selftest (14 offline assertions, no network)
# as a harness CI suite. Auto-discovered by tests/test_bash_suites.py.
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash skills/index-source/scripts/selftest.sh
