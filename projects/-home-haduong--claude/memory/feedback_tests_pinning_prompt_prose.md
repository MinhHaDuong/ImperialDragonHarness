---
name: feedback_tests_pinning_prompt_prose
description: "An adherence test that asserts a sentence exists in a SKILL.md pins the procedure and blocks rewriting it; and a substring assertion passes on a defined-but-never-called helper"
metadata:
  type: feedback
---

Two defects found while cutting `nightbeat-supervisor` from 264 lines of
procedure to a 78-line intent contract (2026-08-14, PR #747).

**1. Tests that assert prose pin the procedure in place.** Three adherence
tests required specific sentences to be present in `SKILL.md` — a literal
`git status --porcelain` snippet, the sentence "Commit tracked writes
immediately", a `settings.json` write-point marker. They passed whether or not
the property held at runtime, and they failed the build for any rewrite of the
procedure, including one that moved the property into code where it is actually
enforced. Neither binding nor verified: the worst of both.

The rewrite went red at 955/5 and *that was the finding*, worth more than the
prose cut. It is the harness's own doctrine (guards over exhortation) inverted
— the ratchet was ratcheting the sediment.

**How to apply:** assert the *property*, in the medium that enforces it. If
commit discipline matters, the pre-commit hook and the next cycle's dirty-tree
pre-flight are the enforcement; a test that greps the prompt adds nothing. When
a test's subject is a prompt, ask what it would catch that a runtime guard
would not. Locate sections by heading *role* (`^##\s+Invariants\b`), never by
an exact heading string — one test hard-matched
`## Invariants (the only prescriptions)` and failed a document that still held
the invariant.

**2. A substring assertion passes on never-called code.** Moving the
stranded-checkout probe from prose into `nightbeat-supervisor-survey.py`, the
retargeted test asserted `"check-primary-checkout" in source`. Deleting the
call from `main()` left it **green** — the helper's own `def` and docstring
satisfy the substring. Fixed by parsing the module and asserting `main()`'s
call graph contains the probe.

**Why:** this is the "all clear indistinguishable from I could not look" trap
from `tickets/AGENTS.md`, reproduced *while* moving a guard from prose into
code — the exact operation that is supposed to make a check real. Only the RED
proof caught it; the test looked correct on inspection.

**How to apply:** when a test asserts that code *runs* something, assert the
call, not the token — `ast.parse` the module and walk the entry point's calls.
And always prove RED by deleting the thing under test, not by reading the
assertion. See [[reference_claude_code_goal_command]] for the primitive this
rewrite was making room for.
