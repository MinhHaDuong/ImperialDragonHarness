---
name: Subagents must follow runbooks
description: When launching agents for ticket work, always instruct them to follow start-ticket and review-pr runbooks
type: feedback
---

When launching a subagent to work on a ticket, always include in the prompt:
- "Follow `runbooks/start-ticket.md` as your entry point"
- "After completing code, self-review following `runbooks/review-pr.md` before opening the PR"

**Why:** Agent working on #279 skipped start-ticket runbook and self-review entirely. It went straight to coding, produced correct code but didn't follow the DD phases (Doing → PR → Review → Iterate). The doc propagation check was also skipped — only caught because the parent reviewed manually. Subagents don't automatically follow runbooks unless explicitly told to.

**How to apply:** Every agent prompt for ticket work must include these two lines. This applies to both `start-ticket` (entry) and `review-pr` (exit). The agent should announce DD phase transitions and self-review its own PR in a fresh context before declaring done.
