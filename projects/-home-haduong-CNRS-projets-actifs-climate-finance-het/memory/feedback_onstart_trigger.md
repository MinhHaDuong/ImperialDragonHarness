---
name: on-start trigger must run automatically
description: The on-start runbook must execute before the first response, without being asked — it's a trigger, not a request
type: feedback
---

Run `runbooks/on-start.md` fully before the first reply in every conversation. Do not wait for the user to mention it.

**Why:** The user had to ask twice — first pointing to the runbook, then calling out that it still wasn't followed. The gate (step 3: branch before proceeding) was announced but not executed.

**How to apply:** At conversation start, read and execute all on-start steps (setup, orient, branch+announce) before responding to the user's message. The branch creation is a hard gate — don't announce a phase without having the branch checked out.
