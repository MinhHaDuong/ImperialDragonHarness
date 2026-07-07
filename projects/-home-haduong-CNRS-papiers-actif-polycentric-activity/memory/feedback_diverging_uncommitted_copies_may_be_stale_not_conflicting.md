---
name: feedback-diverging-uncommitted-copies-may-be-stale-not-conflicting
description: "When the same untracked file sits uncommitted in two checkouts with different content, diff them by date/content before treating it as a live parallel-session conflict — it may just be one stale duplicate of the other."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc2349a2-725b-4756-8875-771442f0f763
---

2026-07-07: `conception/registre-verification-het.md` existed uncommitted in
both the primary checkout and the `t0014` worktree, with different content.
An earlier segment of this same session had already flagged this as
apparent parallel-session WIP and deliberately left it untouched (correct
caution at the time — see [[feedback_raid_for_proofs]] on not touching
other sessions' uncommitted work). When the user later asked to reconcile
it, a plain `diff -u` showed the primary checkout's copy was a strict
superset — dated 07-07 additions (verified source deposits) the `t0014`
copy lacked, itself a stale 07-06 snapshot. No merge was needed, just
picking the newer copy.

**Why:** "uncommitted + diverging across two trees" does not by itself mean
two people are actively editing in parallel. It can just as easily mean the
same content was copied into a second tree earlier and never refreshed —
ordinary drift, not a live conflict. Treating every divergence as
untouchable parallel WIP would have left this ticket-blocking file stuck
indefinitely.

**How to apply:** the "don't touch other sessions' uncommitted work" caution
still applies to *deciding whether to act at all* — get explicit user
direction first, as happened here. But once directed to reconcile, diff the
copies before assuming a conflict: a one-directional superset (all of A's
content plus more, nothing exclusive to B) resolves by taking the newer
copy outright, no merge logic required.
