---
name: feedback_dont_codify_hard_rules
description: Don't codify hard prescriptive rules for judgment-shaped conventions — they make agents lazy; leave the judgment in place
metadata:
  type: feedback
---

Author directive (2026-07-10): **don't codify hard rules for things that are
really judgment calls — hard rules make agents lazy.** When a convention amounts
to "do the sensible thing here" (e.g. "file the editorial decision beside the
submission, wherever it now lives"), spelling it out as a prescriptive rulebook
entry invites an agent to pattern-match the rule and stop reasoning about the
actual situation.

**Why:** the harness rulebook earns its keep on *invariants and failure modes
discovered at cost* (the memory runbook, git discipline, security paths) — things
where getting it wrong is expensive and non-obvious. A filing taxonomy or a
"where does X go" convention is not that: the right home is legible from the
context, and a rule that hardcodes it removes the thinking without removing the
need to think.

**How to apply:** before adding a rule/rulebook entry, ask "is this an invariant
an agent would violate by accident, or a judgment an agent should make each
time?" Only the former gets codified. For the latter, leave it tacit — or at
most a one-line pointer that names the judgment, never a decision table that
substitutes for it. Bit on IDH 0264 (proposed a hard rule for filing editorial
decisions → closed wontfix). Related: [[feedback_skills_just_work_no_config_blocks]].
