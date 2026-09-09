#!/usr/bin/env bash
# Regression test for the rules loading contract (tickets 0042, 0151, 0572).
#
# History, and the reason this file was rewritten on 2026-09-09: it used to
# assert that on-start.sh emits the rules INDEX and not the rule BODIES, and it
# passed for months while the runtime loaded 18 of the 19 bodies into the system
# prompt on its own. The hook was the only channel it could see, so its all-clear
# and "I could not look" were the same output — the failure mode the harness
# names in tickets/AGENTS.md and in ticket 0875.
#
# The contract it now guards:
#   1. on-start.sh emits neither bodies nor the index — the runtime auto-loads
#      `~/.claude/rules/**.md` itself, so anything the hook prints is a second
#      copy (rules/README.md § how they load).
#   2. Every rule file the index lists as conditional actually carries the
#      `paths:` frontmatter that makes it conditional. Without it the file is
#      resident and the index entry is a lie.
set -euo pipefail

cd "$(dirname "$0")/.."
fail=0

out=$(bash scripts/on-start.sh 2>&1 || true)

# 1. Rule-body sentences must not appear in hook output. One distinctive
#    sentence per file; these are resident by other means, never by this hook.
declare -a body_strings=(
  # workflow.md
  "Reviewers use a different model than the coder."
  # git.md
  "Main is read-only except for STATE housekeeping."
  # coding-python.md
  "always \`uv sync\`"
)
for needle in "${body_strings[@]}"; do
  if [[ "$out" == *"$needle"* ]]; then
    echo "FAIL: hook output leaked rule body content: '$needle'"
    fail=1
  fi
done

# 2. The index must not be cat-ed either: the runtime already loads it.
if grep -qE '^[^#]*cat[^#]*rules/README\.md' scripts/on-start.sh; then
  echo "FAIL: scripts/on-start.sh cats rules/README.md — the runtime already"
  echo "      loads it as a resident rule; cat-ing it serves a second copy"
  fail=1
fi
if [[ "$out" == *"Conditional rules — absent until a matching file is touched"* ]]; then
  echo "FAIL: hook output contains the rules index (duplicate of the resident copy)"
  fail=1
fi

# 3. The old skills/harness-rules wrapper must be gone — rules live at the
#    repo root (ticket 0151), loaded by the runtime, not by a skill.
if [[ -e skills/harness-rules/SKILL.md ]]; then
  echo "FAIL: skills/harness-rules/SKILL.md still exists (rules moved to rules/)"
  fail=1
fi

# 4. Index exists.
if [[ ! -f rules/README.md ]]; then
  echo "FAIL: rules/README.md missing"
  fail=1
fi

# 5. Every file the index lists in its conditional table carries `paths:`.
#    Table rows look like: | [coding-python.md](./coding-python.md) | ... |
while read -r rel; do
  [[ -n "$rel" ]] || continue
  if [[ ! -f "rules/$rel" ]]; then
    echo "FAIL: rules/README.md lists rules/$rel, which does not exist"
    fail=1
    continue
  fi
  if ! head -20 "rules/$rel" | grep -q '^paths:'; then
    echo "FAIL: rules/$rel is listed as conditional but has no 'paths:' frontmatter"
    echo "      — without it the runtime loads it in every session"
    fail=1
  fi
done < <(sed -n '/^## Conditional rules/,/^## /p' rules/README.md \
         | grep -oP '^\| \[\K[^]]+')

if (( fail )); then
  exit 1
fi
echo "PASS: rules loading contract holds"
