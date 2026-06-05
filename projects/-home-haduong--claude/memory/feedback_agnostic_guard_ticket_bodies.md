---
name: feedback-agnostic-guard-ticket-bodies
description: "Agnostic-guard catches /home/[a-z] paths in ticket bodies — agents must use ~/path not /home/user/path in ticket examples"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3e1255e4-ffec-4ef7-9b73-843c94d4d4d7
---

Sanitize ticket body examples to `~/<repo>/<file>` not `/home/haduong/<repo>/<file>`.

**Why:** `scripts/check-agnostic.sh` runs on `tickets/` as well as `skills/`. Ticket bodies written with real session paths (e.g. examples of the bug being reported) will fail CI on the first PR that touches those files. Discovered during quickfixes session 2026-05-23 — needed a fixup commit on t170.

**How to apply:** When writing ticket bodies that show path examples, always use `~/<repo>/<file>` or `$HOME/<repo>` instead of the literal `/home/haduong/` prefix. The same rule applies in rules and skills.
