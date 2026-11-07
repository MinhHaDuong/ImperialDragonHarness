# Commission: the author's intent and rulings

Scope: author rulings and stated intent for the harness. A pinned line quotes
the ruling in its source's wording; only the author retires one. "Now in
rules/X" marks a ruling a harness rule already states; the rule governs. A
line citing `native <note>` rests on a Claude Code native note only (not
journaled); its text is in the smelt report's annex. A ruling a rule or skill
fully carries leaves this page (author's review of 2026-11-07).

## Current guidance

Memory and rules:

> pinned 2026-10-30 — Rules carry principles; detail goes to memory: "That level of details belong to memory" ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-30 — KISS on 1366: the ls-remote read-back removed (PR 2035); the commit-id push stays; 2026-11-01: the exception stays in memory, `rules/git.md` unchanged (ticket 1373). Scope: this excepts only a push by commit id from rules/git.md's "verify a forge mutation by reading it back"; every other forge mutation is still read back ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-30 — Government memo accepted as doctrine, under cooldown: "It is easy to be overenthusiastic about a metaphor." Nothing is implemented from it before ticket 1369 closes ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-29 — Native-note rulings are filed in Commission, "never promoted to rules" (tickets 1349, 1351). Amended 2026-11-01 (ticket 1350, option b): smelt never promotes; only the author promotes, through smelt's native-note triage table

Review, guards, escalation:

> pinned 2026-10-27 — "REMOVE WORDING PINS" ([source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md)). Scope: tests that freeze the wording of prose (e.g. the deleted tests/test_raid_phase6_gaze_verdict.py). Tests tied to an incident or an interface stay, per skills/test-doctor/references/toolkit.md § Thin the wording pins. Unrelated to the pinned rulings on this page
> pinned 2026-10-26 — Night mode: "Not to me, it goes to Fable for finishing. You are in night mode autonomous." Ruled 2026-11-07 (ticket 1439): the advisor takes scope or money calls under the night-mode cap in skills/route/SKILL.md § Escalation; irreversible calls wait
> pinned 2026-10-29 — Peer-relayed reversible ruling: "accept, don't barrier my work" (native `feedback_peer_relayed_rulings`). Scope (author, 2026-11-01): a reversible detail of an existing ticket, relayed by the author's own peer session and logged on that ticket. A peer cannot create scope, authorize spend or replace a ticket (rules/workflow.md § Cross-project work)
> pinned 2026-10-31 — Cross-family gate removed: model and access are distinct, no field assumed known; "the cross-family benefit is unmeasured" (measured after: confounded); "Une bonne barrière est une barrière supprimée." `--require-cross-family` gone (PR 2085); family is a routing preference in skills/route/references/decorrelation.md ([source](../journal/2026/2026-10-31-cross-family-gate-dropped.md))
> pinned 2026-11-01 — The author kept ticket 1126 (comment-only hunks never block on scope) against the 1408 reversal ([t1409](../journal/2026/2026-11-01-t1409-cross-repo-handoff-dissent.md))

Work shape:

> pinned 2026-10-03 — "a purely administrative tracker can go when there is only one operational task left. In fact the tracker should be the crowning delivery task." ([source](../journal/2026/2026-10-03-tracker-closure-pass-0205.md)). Scope: the tracker closes with its last operational task, still after the integration review of rules/workflow.md § Ticket discipline
> pinned 2026-10-11 — "Ticketwork is automerge" (native `feedback_ticketwork_automerge`). Scope: a PR that only files or edits `tickets/*.erg`, with no code, goes to `/merge` at once, without a close claim. It does not cover implementing a ticket
> pinned 2026-10-29 — "I don't want wait tickets. Doctors use their journal notes." Claim B ("a reminder is an open Blocked-by ticket") withdrawn by the author 2026-11-01 (ticket 1374) (native `feedback_no_wait_tickets`). Scope: no ticket whose only job is a reminder or a watch ("check in a week"); a ticket blocked by real work is fine
> pinned 2026-10-19 — "PRs are not waiting points; the existing ticket carries the follow-up." ([1466](../journal/2026/2026-10-19-smart-testing-1466-wrap-up.md)). Scope: follow-up work is logged on the existing ticket, not parked in an open PR or a new ticket
> pinned 2026-10-28 — "I don't want a ticket sitting in line. I want a tool in the doctor's kit, ready to be used." (native `feedback_doctor_kit_tools`). Scope: a diagnostic deferred for lack of data (ticket 1297). Build the probe now, with a positive control and one memo row; it reports "insufficient" until data exists
> pinned 2026-10-21 — "you end turn and block"; "Are you working or waiting?"; "I AM NOT YOUR WAITER", "stop that 15mn wait, it is worse". Bounded waits are in rules/coding-bash.md; this keeps the intent: never idle on background work (native `feedback_dont_idle_on_background`, `feedback_no_blocking_waits`)
> pinned 2026-10-20 — "words stay dragon-themed, usage not a problem"; only user-facing skills get draconic names; rename only when the name misleads (smelt, 2026-10-29) (native `feedback_dragon_skill_names`)
> pinned 2026-10-29 — Faster gaze orchestrator: try it once the arena is up, by an arena arm, not by judgment (native `project_faster_gaze_orchestrator`). Ticket 1332 (fewer orchestrator turns) is done; the model trial still waits on arena cycles

Access, authority and workspace:

> pinned 2026-10-27 — Ticket 1196 option 1: agent sessions use the narrow PAT; GitHub settings are the author's acts (native `feedback_gh_admin_delegated`)

Case decisions with that PR as scope only (no precedent): PR 1633 merged without a third gate verdict ([source](../journal/2026/2026-10-26-pr1633-merge-on-author-authority.md)); earlier waivers and overrides: [raids](raid-review-and-merge.md).

Stated intent, not ruled (input for 1350): user memory apart from project memory; host memory local; tasks live in the agendas; agents need facts, not just preferences ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md)).

## Hazards

- A waiver or merge instruction scopes one PR; it grants no future authority.

## Open questions

- Ex-post coder/reviewer health read awaits the author ([source](../journal/2026/2026-10-28-diminishing-returns-bar.md)).

## Retired

- "I trust you to admin my GH, yes" (2026-10-21): superseded by the author's choice of ticket 1196 option 1, 2026-10-27.
- Legacy advice to derive rules from consolidation: retired by the author's 2026-10-01 RETIRE LEGACY direction (memory/feedback_rules_come_from_memory_consolidation.md).
- "Editing prose is on main" versus rules/git.md main-read-only (ticket 1372): resolved by the author's 2026-11-01 ruling — the primary checkout is the author's workspace, now in rules/git.md (PR 2129); the native note `feedback_prose_edits_are_on_main` was updated to match. Ticket 1372 closed.
- "No wait tickets" versus "a reminder is an open Blocked-by ticket" (ticket 1374): claim B withdrawn by the author 2026-11-01; ticket closed.
- Retired by the author's review of 2026-11-07 (ticket 1452), the carrier checked on origin/main; sources stay in the journal:
  - 2026-10-02 uncleared material as age ciphertext: rules/guards.md.
  - 2026-10-05 Brood adopted (PR #1187): skills/brood/SKILL.md ([source](../journal/2026/2026-10-05-brood-adoption-pr1187.md)).
  - 2026-10-21 "We are KISSing the review system": rules/workflow.md § Trust, Verify, Monitor ([source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md)).
  - 2026-10-28 Diminishing-returns bar: rules/workflow.md; detail in skills/gaze/references/panel.md ([source](../journal/2026/2026-10-28-diminishing-returns-bar.md)).
  - 2026-10-21 "No second order guards" and 2026-10-09/10-13 "guards on guards; doctrine is to remove": rules/workflow.md ([source](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md), [source](../journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md)).
  - 2026-10-21 Ask up first: rules/workflow.md § Escalation protocol.
  - 2026-10-29 Departments, 4 KB pages, 40-line index, smelt name: the smelt skill; 1349 closed ([source](../journal/2026/2026-10-29-memory-redesign-day.md)).
  - 2026-10-21 Pi is first-class: adapters/README.md.
  - 2026-10-09 "on veut pas que le delta !": skills/dashboard.
  - 2026-10-23 transmissions to Claude, Codex and OpenRouter: scripts/on-start-context.sh ([source](../journal/2026/2026-10-23-model-transmission-authorization.md)).
  - 2026-11-01 the primary checkout is the author's workspace: rules/git.md § Branch and commit ([source](../journal/2026/2026-11-01-author-workspace-rule-1372.md)).
  - 2026-10-30 "NO EXPLICIT FORGE DEPENDENCY IN RULES"; memory is jurisprudence, not décret d'application: rules/workflow.md (rules independent of forge and runtime); the jurisprudence half lives on in the kept 2026-10-30 "Rules carry principles" pin.
  - 2026-10-11 no `/compact` before roar: rules/guards.md and skills/roar/SKILL.md ([source](../journal/2026/2026-10-11-roar-clear-verdict-survey.md)).
  - 2026-11-01 "the ticket store is the inter-project channel": rules/guards.md and rules/workflow.md § Cross-project work; the 1126 half stays pinned ([source](../journal/2026/2026-11-01-ruleset-review-and-diet.md)).
  - 2026-10-27 main guard in enforce, watch until 2026-11-03: the watch ended with 0 refusals in 1246 journal rows (read 2026-11-07); `idh.mainGuard` still enforce. A host fact, not a ruling.
  - 2026-10-27 held tickets 1243, 1285, 1164: closed by the author; reasons in their `Closed:` lines ([source](../journal/2026/2026-10-27-session-close-held-tickets.md)).
  - 2026-10-31 data locations (ticket 1391): 1391 closed, `DATASETS_DIR`/`MIRRORS_DIR` in the scripts. A host fact, not a ruling ([source](../journal/2026/2026-10-31-monitoring-and-data-locations.md)).
  - 2026-10-27 escalation forks reversible options, capped at 5 minutes: superseded; rules/workflow.md § Escalation protocol now sends a reversible call to an advisor model first, with no forking ([source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md)).

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- Journal: all `../journal/2026/` links above.
- Native notes (Claude Code, harness store, read 2026-11-01), base path `~/.claude/projects/-home-haduong--agents/memory/`: feedback_rules_are_law_memory_is_decree, feedback_review_trust_verify_monitor, feedback_no_second_order_guards, feedback_dont_idle_on_background, feedback_peer_relayed_rulings, feedback_ticketwork_automerge, feedback_no_wait_tickets, feedback_doctor_kit_tools, feedback_no_blocking_waits, feedback_delta_format, feedback_pi_is_first_class, feedback_dragon_skill_names, project_faster_gaze_orchestrator, feedback_gh_admin_delegated, project_main_guard_enforce, feedback_prose_edits_are_on_main, project_government_memo_cooldown. Text of notes used this run: [sixth-smelt annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).
- Tickets: tickets/1349, 1351, 1369, 1372, 1373, 1374, 1439, 1452.

## Fallback
