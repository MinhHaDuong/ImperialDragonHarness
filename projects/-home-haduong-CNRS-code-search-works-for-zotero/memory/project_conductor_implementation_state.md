---
name: project-conductor-implementation-state
description: "Where the five-tranche conductor scheduler (ticket 0550) stands as of 2026-09-01 — what's merged, what's parked, what's still missing before an end-to-end index build works"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7dbffd44-66ae-4f29-8294-15df4a99ecc2
  modified: 2026-09-01T15:32:26.666Z
---

Tracker: ticket 0550 (fork `MinhHaDuong/zoteus`). As of 2026-09-01:

**Merged** (search-works-for-zotero `main`, code on fork branches, not yet
merged to the fork's own `main` — deliberately, "the fork accumulates"):
0551 (ledger schema + reconcile tick + three fixtures, `tranche-1-ledger-schema`),
0552 (conductor election + lease, `tranche-2-conductor-election`),
0556 (v2 content schema — `entries`/`slabs`/`passages`/FTS in
`search-index-v2.sqlite`, parallel to v1, `tranche-schema-v2-content`).

**Parked, not lost:** 0553 (extract shim). Fork branch
`tranche-3-extract-shim` @ `ff1d41a` is safe. Two real, independently
reproduced concurrency bugs blocked it: a claim-race where a released
(not dead) worker's late completion silently clobbers a second worker's
result, and a truncation-detection gap for a stream cut after `content`
closes but before the trailing page-count fields arrive. PR #156 carries
the full record; `Ticket-ref:` not `Ticket:` so a routine merge won't
auto-close 0553.

**Filed this session, not started:**
0565 (wire seg/1 into the conductor's write loop — no ticket owned this
integration seam until now, `Blocked-by: 0028, 0556`),
0566 (assemble tick+conductor+extract+chunk/embed into one runnable
process — the ticket that actually delivers "point at a fixture library
and index it", `Blocked-by: 0554, 0565`),
0567 (found by the roar sweep: `Ledger.markDone`/`markFailed` lack the
same CAS ownership check `claim()` has — fixing this at the shared
primitive removes 0553's blocker #1 for free when it resumes).

**Real gap that isn't 0553's fault:** SPEC.md's content schema
(entries/slabs/passages) had no code owner among the open tickets before
0556 was filed — 0028 builds the segmenter *algorithm*, 0034 is an
upstream *issue draft*, neither writes the schema. Same shape of gap as
0567: check who actually owns the wiring, not just the two things being
wired.

**Parallel work, another session:** the segmenter family (0028, blocked
on 0502's spec propagation, with children 0557-0564 covering PDF layout,
vendoring pdf.js, heading heuristics, byline detection) is being built
concurrently — not this session's doing, don't assume it's further along
than its own tickets say.

Next real step for the "point at a fixture library" goal: 0553 needs an
actual concurrency-safety fix (not another review round — see
[[feedback-review-rounds-dont-fix-code]]), then 0554, then 0565, then
0566.
