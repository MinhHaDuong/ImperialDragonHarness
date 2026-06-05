---
name: verify gate requires ticket reference in PR body
description: /verify gate fails at phase 1 if PR body has no tickets/*.erg reference — create ticket before opening PR
type: feedback
originSessionId: b5599bd1-d4fd-4cfe-91f4-320d025a2f4a
---
Create the ticket file and add a `**Ticket:** tickets/<name>.erg` line to the PR body *before* opening (or immediately after opening) the PR. The /verify gate reads the PR body for a ticket path and stops at phase 1 if none is found.

**Why:** PR #3 triggered an ESCALATE during /verify because the PR body referenced no ticket. Had to create ticket 0010 retroactively and update the PR body mid-flow.

**How to apply:** When opening a PR in this repo, always include a Ticket line in the PR body pointing to the relevant .erg file.
