---
name: locale-fr-floats-in-guarded-scripts
description: awk/printf float output is locale-dependent — this machine's fr_FR emits decimal commas that break test guards; pin LC_ALL=C at script top
metadata:
  type: feedback
---

`awk 'BEGIN{printf "%.1f", …}'` and shell `printf %f` honor `LC_NUMERIC`, and
this machine runs `fr_FR`, so they emit `70,0` where a test guard expects
`70.0`. Ticket 0358 sat misdiagnosed as three broken credential suites when
the surviving failure was this artifact (fixed in PR #693 by `export LC_ALL=C`
at the top of `skills/reviewers/reviewers.sh`).

**Why:** a locale-dependent failure reproduces on the author's machines but not
in CI (C locale), so it reads as flaky or as a logic bug, and the ticket
inflates. A partial in-script patch is a tell — reviewers.sh already had a
per-call `LC_ALL=C` on one awk while three siblings were unprotected.

**How to apply:** any script whose numeric output is parsed or test-guarded
gets one `export LC_ALL=C` right after `set -euo pipefail`, never per-call
prefixes. When a guard reports a missing expected number, diff the actual
output for `,` vs `.` before suspecting the logic. Related: [[rtk-rewrites-git-output]]
for the other class of "output not what the parser expects".
