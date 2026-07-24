---
name: Beat agent SSH-to-padme blind spot
description: Beat agents incorrectly exclude tickets that say "SSH to padme" — but beat always runs on padme
type: feedback
originSessionId: f66e55c9-026e-404f-b730-645154cd3bf4
---
Beat agents have incorrectly excluded tickets citing "Requires SSH to padme" as an external dependency, when beat.py always runs on padme itself.

**Why:** The ticket body was written from the perspective of a developer sitting at doudou who needs to SSH to padme. When the beat agent reads that instruction, it treats SSH as a blocker. But beat.py runs on padme — SSH is already satisfied.

**How to apply:** When pick-ticket or orchestrator sees "SSH to padme" or "run on padme" in a ticket body, treat it as a no-op constraint. The beat always executes on padme. Check whether the data paths exist locally before concluding a ticket is unrunnable.

Also: stale data paths in ticket bodies (e.g. `/home/haduong/CNRS/papiers/actif/...`) may have moved — check the script defaults before rejecting the ticket.
