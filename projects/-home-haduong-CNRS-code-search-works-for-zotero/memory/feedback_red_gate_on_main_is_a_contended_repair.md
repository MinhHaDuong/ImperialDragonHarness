---
name: feedback_red_gate_on_main_is_a_contended_repair
description: "A failing check on main is visible to every parallel session at once, so repairing it is a race — re-run the check immediately before pushing, and don't file the ticket until you know you're the one fixing it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4cf68015-1008-48c8-aa04-23ab753888d5
  modified: 2026-09-06T21:50:36.815Z
---

A red gate on `main` is not your finding. It is a **broadcast**: every parallel
session in the repo runs `make check` too, sees the same failure, and several
will independently fix it. Repairing it is therefore contended work, and the
contention is invisible — unlike a ticket, nothing assigns it.

Cost, 2026-09-06 (ticket 0714 raid): the wrap-up `make check` on main was red on
`check_ticket_logs.py`, four log stamps in tickets 0029 and 0719 naming a time
after the commit that wrote them. I walked each line's introducing commit, filed
ticket 0724, corrected all four, committed, pushed, and opened PR #410. While it
sat there a sibling session landed byte-identical corrections — the same four
values, arrived at the same way. The whole PR was redundant on arrival: closed,
branch deleted, ticket 0724 dropped unfiled. Roughly a dozen tool calls for
nothing, and a ticket that would have been noise in the store.

The open-PR scan I ran first was not wrong, and that is the point worth keeping:
it was a **snapshot**. It listed three open PRs, none touching those tickets. The
sibling's PR was opened *after* the scan and merged before my push. A scan of
open work answers "who is doing this now", and the answer expires immediately.

**Why:** the severity floor says findings that block a merge get fixed, and a red
main blocks everyone — so the incentive to fix it fast is exactly what makes
several sessions fix it at once. Speed is right; the duplication is the tax.

**How to apply:**

- Re-run the *specific* failing check against a fresh `origin/main` immediately
  before you push the repair. Green means someone beat you: stop, delete the
  branch, and say so. This costs one command and catches most of the race.
- Do not file a ticket for a shared-metadata repair until the fix is pushed and
  you know it is yours. A ticket for a repair someone else completed is noise,
  and dropping it unfiled is cheaper than closing it.
- The window is the whole life of the branch, not just the moment you start —
  my scan and my push were minutes apart and the frontier moved between them.
- This applies to repo-wide hygiene (log stamps, lint, stale refs), never to
  your own ticket's work, which nobody else is doing.

Related: [[feedback_stage_by_path_in_shared_checkouts]],
[[feedback_append_only_merge_union]], [[feedback_green_prs_red_union]].
