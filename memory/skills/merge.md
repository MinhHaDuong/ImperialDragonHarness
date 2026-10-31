# merge — cases
Updated: 2026-10-31 · skill version: cf514383

## Latest — 2026-10-31
Context: three merges (PR 2065, 2066, 2085) in one interactive session, the last removing the cross-family gate. What happened: on PR 2085's fix round (a same-family seat only), main's verify-gate refused admission with "no cross-family seat", applying the rule the PR removes; `raid_land.py` also warned on all three that the attribution block could not be rendered. Reaction: a re-gaze with an OpenAI seat cleared it, and verify-gate APPROVED in round 1; attribution was captured from notes. Outcome: merged at 7d546daf, d704081a, 95ede53f. Source: memory/journal/2026/2026-10-31-cross-family-gate-dropped.md.

## Usual
Context: a merge request with a close claim and a gate record. What happened: the helper refuses while CI runs and succeeds on retry; a bare or short `Ticket:` claim is rewritten to name the ticket path. Of the last 400 merged PRs to 2026-10-13: 196 close claims, 155 `Ticket: none`, 86 `Ticket-ref`, 16 no ticket text (derived counts, may overlap). Reaction: fix the claim line, retry. Outcome: no dropped claims in the period. Source: memory/topics/raid-review-and-merge.md § Merge mechanics.

## Best — 2026-10-27
Context: raid afternoon, about 45 PRs merged. What happened: the before-merge gate shrank to about 13 s, the full suite ran after the merge, landing went through `scripts/raid_land.py`; #1774 took 10m26s from first review to merge. Reaction: the author said "Stay optimistic. Trust, Verify, Monitor." Outcome: main green at dd222149. Caveat from the same run: `/merge` step 8 (sync local main) was skipped on the first 13 merges, so helpers ran from a stale primary checkout. Source: memory/journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md.

## Worst — 2026-10-30
Context: the after-merge gate record for main tip 0645f247 reached local `refs/notes/gate` but never origin's, with no warning logged. What happened: a forced notes fetch from another process sharing the repository rewound the ref, so a push by ref name exited 0 and sent nothing. Reaction: raid 85542d reproduced it with a bare remote; PR 2033 pushes by commit id and reads the remote back. Outcome: fixed by 1493043e (ticket 1366); a recurrence now logs a warning. Status: fixed. Source: memory/journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md.
