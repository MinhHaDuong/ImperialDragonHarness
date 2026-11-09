# Ticket 1472: deferred label applied, then reverted at the author's request

Date: 2026-11-09. PRs 2277, 2278, 2279 (all ticket-only, bookkeeping tier).

Context: PR 2277 filed ticket 1472 (retire the cross-PR collision gate once
git-erg ID claims land). `erg ready` then listed it although its body says it
is not actionable until a git-erg release carries the claims.

Events: the session noted this and offered to mark it. The author replied
"Sill waiting"; the session read that as assent and landed PR 2278, adding
`Label: deferred` (the only lever that hides a ticket from `erg ready`; a
cross-repo `Blocked-by` only warns). The author answered "Undo that. The plan
is to run it as soon as the erg conversation delivers." PR 2279 removed the
label; the ticket log keeps both lines.

Outcome: 1472 is on the ready list, as the author intends. Decision made by
the author: a ticket waiting on a live sibling conversation stays ready.
