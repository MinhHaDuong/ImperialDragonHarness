# Raid — merge-permission denial

Loaded from `skills/raid/SKILL.md` § Merge-permission denial.

The permission layer may decline an APPROVED PR's merge because the review
is insufficiently independent of its author. Inspect the stated objection
and the actual producer/reviewer identities; do not assume that a launched
reviewer supplied independent evidence. Never weaken permissions, skip checks
or hand-merge around the guard.

1. Do not retry the denied call verbatim.
2. Request independent review of the current PR head through the active
   runtime, using `skills/reviewers/SKILL.md` and its live-route reference.
   Describe the expertise, capability and independence needed to answer the
   objection. Let the runtime discover and route a suitable reviewer; record
   the actual identity, route, independence basis, reviewed base/head and
   completed report. While the PR's gate budget has a round left (fewer than
   two verify-gate rounds posted, § Phase 6), disposition every returned
   finding through verify-gate; a blocking finding sends the PR back through
   Phase 6. When the gate budget is exhausted, run no further gate or fix: park
   the PR and escalate to the author with the findings (step 4). If fixes change the
   head, refresh the independent evidence before retrying. Preserve failed or
   missing review records and `PANEL-INTEGRITY:` verbatim in the external
   verdict record; they are coverage limitations, not findings to disposition.
3. Only when completed independent evidence answers the stated objection and
   findings have a clean disposition, post that evidence and its disposition
   on the PR. Quote the verdict and this recovery contract in the transcript
   and retry the merge once. A claimed route or empty response is insufficient.
4. If independent evidence is unavailable or insufficient, or the retry is
   denied, park the PR merge-ready, continue the wave, and name each parked
   PR, the unresolved objection and deferred post-merge steps (cleanup +
   per-PR roar) in the briefing. Optional external review's fail-open policy
   does not waive a merge denial; do not bypass the permission layer.
