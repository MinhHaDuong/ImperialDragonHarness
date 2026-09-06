---
name: one-liner-no-ticket
description: "Author ruling 2026-09-06 — a one-line probe fix is a hotfix PR with \"Ticket: none\", never a ticket; ticket only what needs a handoff"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c237237f-abd3-4b9c-94b8-0f98e597a30a
  modified: 2026-09-06T16:40:00.711Z
---

When a defect's fix is a one-liner (the sdt_read.block_text recursion, PR #399), the author wants it hotfixed directly on a branch with `**Ticket:** none`, not filed as a ticket first. His words: "A oneliner does not deserve a ticket."

**Why:** a ticket is a handoff document; a one-line fix has nothing to hand off, and the queue already runs 59 ready / 31 blocked. Filing it costs more than fixing it and adds to the backlog the severity floor exists to shrink.

**How to apply:** when a probe or sweep surfaces a defect whose fix fits in one commit you can write now, cut `hotfix-<slug>` from origin/main, fix + test (with the red control), open the PR with `Ticket: none`, merge. Reserve tickets for work that needs a second session or an author decision. Related: [[guard-budget-is-net-negative]], [[the-tickets-own-test-needs-a-control]].
