---
name: feedback_no_direct_push_main
description: "all commits go through a PR on git-erg — no direct push to main, even for ticket lifecycle files"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 76fda995-7a90-4d73-8bd9-1acc840f289f
---

Never push directly to `origin/main` on git-erg, even for ticket lifecycle commits (new `.erg` files, `erg close`, `erg archive`).

**Why:** The permission model has no reliable carve-out for ticket-only commits. The `workflow.md` exception ("ticket lifecycle may land directly on main") is aspirational but not operational on this repo — the user cannot make the permission allow-list work reliably for this case.

**How to apply:** Ticket files created during a raid or celebrate must travel on a branch and land via PR. The bundling rule still applies: commit the ticket file on the same branch as the spawning work (per [[bundle_follow_up_tickets]]), not as a standalone push to main. If a ticket needs to be filed after a branch is already merged, open a tiny dedicated branch + PR.
