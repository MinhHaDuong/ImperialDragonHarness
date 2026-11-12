# Author's jurisprudence rulings on the IDH project

## On memory and rules:

Rules carry principles; detail goes to memory: "That level of details belong to memory" ([context](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))

KISS on 1366: the ls-remote read-back removed (PR 2035); the commit-id push stays; 2026-11-01: the exception stays in memory, `rules/git.md` unchanged (ticket 1373). Scope: this excepts only a push by commit id from rules/git.md's "verify a forge mutation by reading it back"; every other forge mutation is still read back ([context](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))

Government memo accepted as doctrine, then put under cooldown: "It is easy to be overenthusiastic about a metaphor." The cooldown ended with the author's triage, closing 1369 on 2026-11-10 ("defaults"): F1, F2, F4, F6 dropped; F3 wanted, not now; F5 wanted, host facts only; correcting the memo's stale claims is a need, done as a dated note at its top ([context](../journal/2026/2026-10-30-rulings-and-memory-design-input.md), [triage](../journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md))

## On review, guards, escalation:

"REMOVE WORDING PINS" ([context](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md)). Cull tests that freeze the wording of prose (e.g. the deleted tests/test_raid_phase6_gaze_verdict.py). Case 2026-11-09: a new source-string test on an APPROVED head was removed before landing, then an older pin too: "Remove it too. Unbend this PR prose" (PR 2367, [context](../journal/2026/2026-11-10-roar-pr2367-housekeeping-notes-pins-removed.md))

Night mode: "Not to me, it goes to Fable for finishing. You are in night mode autonomous." Ruled 2026-11-07 (ticket 1439): the advisor takes scope or money calls under the night-mode cap in skills/route/SKILL.md § Escalation; irreversible calls wait

Peer-relayed reversible ruling: "accept, don't barrier my work" ([smelt annex: `feedback_peer_relayed_rulings`](../smelts/2026-11-01-sixth-smelt-native-notes.md)). Scope (author, 2026-11-01): a reversible detail of an existing ticket, relayed by the author's own peer session and logged on that ticket.

"Une bonne barrière est une barrière supprimée." Case: "the cross-family benefit is unmeasured" (measured after: confounded); Outcome: `--require-cross-family` gone (PR 2085); family is a routing preference in skills/route/references/decorrelation.md ([context](../journal/2026/2026-10-31-cross-family-gate-dropped.md))

## On work shape:

"A purely administrative tracker must go when there is only one operational task left. A tracker should be the crowning delivery task." ([context](../journal/2026/2026-10-03-tracker-closure-pass-0205.md)). Reasoning: an empty tracker only helps when there are more than 2 dependents. Otherwise close it in favor of its last operational task.

"Ticketwork is automerge" ([smelt annex: `feedback_ticketwork_automerge`](../smelts/2026-11-01-sixth-smelt-native-notes.md)). Scope: a PR that only files or edits `tickets/*.erg`, with no code, goes to `/merge` at once, without a close claim. It does not cover implementing a ticket.

"I don't want wait tickets. Doctors use their journal notes." Case: explicit retract of "a reminder is an open Blocked-by ticket" on 2026-11-01 (ticket 1374) ([smelt annex: `feedback_no_wait_tickets`](../smelts/2026-11-01-sixth-smelt-native-notes.md)). Scope: no ticket whose only job is a reminder or a watch ("check in a week"); a ticket blocked by real work is fine.

"Undo that. The plan is to run it as soon as the erg conversation delivers." Case: a `deferred` label added to 1472 on a read of "Sill waiting" as assent, reverted (PR 2279). Scope: a ticket waiting on a live sibling conversation stays on the ready list ([context](../journal/2026/2026-11-09-1472-deferred-label-applied-and-reverted.md))

"PRs are not waiting points; the existing ticket carries the follow-up." ([context](../journal/2026/2026-10-19-smart-testing-1466-wrap-up.md)). Scope: follow-up work is logged in existing or new tickets, not parked in an open PR. Rationale: Short-lived branches principle.

"I don't want a ticket sitting in line. I want a tool in the doctor's kit, ready to be used." ([smelt annex: `feedback_doctor_kit_tools`](../smelts/2026-11-01-sixth-smelt-native-notes.md)). Scope: a diagnostic deferred for lack of data (ticket 1297). Decision: Build the probe now, with a positive control and one memo row; it reports "insufficient" until data exists

"you end turn and block"; "Are you working or waiting?"; "I AM NOT YOUR WAITER", "stop that 15mn wait, it is worse". Bounded waits are in rules/coding-bash.md; this keeps the intent: never idle on background work ([smelt annex: `feedback_dont_idle_on_background`, `feedback_no_blocking_waits`](../smelts/2026-11-01-sixth-smelt-native-notes.md))

"words stay dragon-themed, usage not a problem"; only user-facing skills get draconic names; rename only when the name misleads (smelt, 2026-10-29) ([smelt annex: `feedback_dragon_skill_names`](../smelts/2026-11-01-sixth-smelt-native-notes.md)). 2026-11-09: object skills carry their directory's name (`/paper`, `/mission`, `/post`); dragon verbs stay for the harness working on itself ([context](../journal/2026/2026-11-09-raid-1483-paper-skill.md))

## On tools and evidence:

Zotero identity, 2026-11-10 (tickets 1510, 1511): "Multiple DOI and multiple ISBN is the norm." (the unattended sweep keeps no contradiction refusal); "Unreliable does not means never use, but use cautiously. LLM judgement can be made." (embedded PDF titles stay a hint; `find-work --metadata` unchanged); "A good" (the hand command `suggest-attachments --edit` refuses on a differing given identifier, with a way out: record the second identifier and rerun) ([context](../journal/2026/2026-11-10-roar-raid-13f6d8-zotero-attach-licence-and-embedded-title.md))

## On access, authority and workspace:

Agent sessions use the narrow PAT; GitHub settings are the author's acts ([smelt annex: `feedback_gh_admin_delegated`](../smelts/2026-11-01-sixth-smelt-native-notes.md), ticket 1196 option 1)

A waiver or merge instruction scopes one PR; it grants no future authority. It is smelt's job to scope case decisions beyond their PR ([context](../journal/2026/2026-10-26-pr1633-merge-on-author-authority.md), [raids](raid-review-and-merge.md)).
