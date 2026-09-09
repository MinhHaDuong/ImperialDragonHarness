#!/usr/bin/env bash
# Structural regression test for ticket 0045 — orchestrator → raid rename.
# Asserts that no live skill, script, or doc still uses the /orchestrator
# slash command, while ticket history remains untouched.
#
# It also checked that the nightbeat log parser dual-accepted both label
# prefixes. Ticket 0882 removed that parser with the rest of the nightbeat
# block, so nothing reads those labels any more and the check went with it.
set -euo pipefail

cd "$(dirname "$0")/.."
fail=0

# 1. No /orchestrator slash invocations in live surfaces
hits=$(grep -rn '/orchestrator' skills/ scripts/ commands/ README.md STATE.md bin/ 2>/dev/null || true)
if [[ -n "$hits" ]]; then
  echo "FAIL: /orchestrator still referenced in live code:"
  echo "$hits"
  fail=1
fi

# 2. Ticket history preserved (/orchestrator remains in old tickets)
ticket_hits=$(grep -rln '/orchestrator' tickets/ 2>/dev/null | wc -l)
if (( ticket_hits < 1 )); then
  echo "FAIL: expected /orchestrator references in tickets/ (history); found $ticket_hits"
  fail=1
fi

# 3. Skill directory renamed
if [[ -e skills/orchestrator ]]; then
  echo "FAIL: skills/orchestrator still exists"
  fail=1
fi
if [[ ! -f skills/raid/SKILL.md ]]; then
  echo "FAIL: skills/raid/SKILL.md missing"
  fail=1
fi
if ! grep -q '^name: raid$' skills/raid/SKILL.md; then
  echo "FAIL: skills/raid/SKILL.md frontmatter name is not 'raid'"
  fail=1
fi

if (( fail )); then
  exit 1
fi
echo "PASS: orchestrator → raid rename is structurally consistent"
