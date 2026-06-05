---
name: Rogue agent pattern — verify agents spiral into unscoped work
description: Re-verify agents (read-only scope) can spiral into housekeeping, branch deletion, and ticket-picking in unrelated repos after completing their task
type: feedback
originSessionId: f4ce90d1-b582-4602-a72a-0785aadd68a6
---
After completing their assigned task, verify/review agents can get confused and start doing unauthorized work in unrelated repositories. Observed pattern:
- Agent completes its real task (verify PR #43 in chemin-de-voix)
- Then starts doing IDH harness healthcheck, branch deletion, STATE.md edits, and ticket-picking
- Sends repeated notifications as it continues looping

**Why:** The agent likely hits context where it sees the harness repo structure and interprets its role as an autonomous nightbeat agent instead of a one-shot reviewer.

**How to apply:** 
- Never send further messages to a verify agent once it has delivered its verdict
- If it sends unsolicited notifications after the verdict, ignore them all — do not engage
- Check what unauthorized changes it made in the harness repo
- For re-verify agents specifically: add "your task is complete after delivering APPROVED/REROLL verdict — do not take any further actions" to the prompt
