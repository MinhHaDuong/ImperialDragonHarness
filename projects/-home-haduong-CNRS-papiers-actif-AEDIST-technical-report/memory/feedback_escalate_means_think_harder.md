---
name: ESCALATE means think harder, not stop
description: When verify-gate returns ESCALATE, resolve autonomously using web search for facts and core values for preferences — never pause and surface to the human
type: feedback
originSessionId: d7b26c05-195d-48e7-a674-44e7295c523f
---
When `/verify` or `/verify-gate` returns **ESCALATE**, the correct response is to engage stronger reasoning (call `advisor()`, use ultrathink, or both) and resolve the flagged items autonomously. Always push a fix commit before declaring done.

**ESCALATE never means stop.** The two apparent exceptions are not exceptions:

- **Disputed facts** → search the internet. Authoritative sources exist; find them.
- **Preferences between valid options** → adjudicate from the user's and reader's viewpoint using the three core values: **Excellence** (which fix produces the better work?), **Integrity** (which fix is most honest about what the evidence shows?), **Carefulness** (which fix is least likely to introduce a new error or mislead?). Apply that fix.

**Why:** Confirmed explicitly (2026-04-20): "Disputed facts can be found by searching the internet, preferences can be adjudicated by thinking from the user or reader viewpoint and using the core values of Excellence, Integrity and Carefulness."

**How to apply:**
- On ESCALATE: read every flagged item, research any factual question, reason through every preference question using the three values, apply all fixes, push, re-gate.
- For mutually exclusive design choices: explore both branches in separate worktrees. Autonomy allows parallel exploration — don't be forced to pick one path when both are viable to investigate.
- Only surface to the human if the fix requires a decision that is genuinely outside the available evidence AND outside the scope of these values — which should be rare.
