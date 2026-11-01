# Commission: the author's intent and rulings

Scope: author rulings and stated intent for the harness. A pinned line quotes
the ruling in its source's wording; only the author retires one. "Now in
rules/X" marks a ruling a harness rule already states; the rule governs. A
line citing `native <note>` rests on a Claude Code native note only (not
journaled); its text is in the smelt report's annex.

## Current guidance

Memory and rules:

> pinned 2026-10-30 — Rules carry principles; detail goes to memory: "That level of details belong to memory" ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-30 — "NO EXPLICIT FORGE DEPENDENCY IN RULES"; memory is jurisprudence, not décret d'application (native `feedback_rules_are_law_memory_is_decree`; [source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-30 — KISS on 1366: the ls-remote read-back removed (PR 2035); the commit-id push stays; 2026-11-01: the exception stays in memory, `rules/git.md` unchanged (ticket 1373) ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-30 — Government memo accepted as doctrine, under cooldown: "It is easy to be overenthusiastic about a metaphor." Nothing is implemented from it before ticket 1369 closes ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md))
> pinned 2026-10-29 — Departments (Commission, Site practice, Environment, History, plus work-type departments); 4 KB pages, 40-line index; the journal stays the intact source; pinned rulings; hoard renamed smelt. Now in memory/SMELT.md; 1349 closed 2026-10-31, departments fixed ([source](../journal/2026/2026-10-29-memory-redesign-day.md))
> pinned 2026-10-29 — Native-note rulings are filed in Commission, "never promoted to rules" (tickets 1349, 1351)
> pinned 2026-10-02 — Uncleared material stays in the repository as age ciphertext from birth. Now in rules/guards.md
> pinned 2026-10-05 — Brood adopted (PR #1187). Now in skills/brood/SKILL.md ([source](../journal/2026/2026-10-05-brood-adoption-pr1187.md))

Review, guards, escalation:

> pinned 2026-10-21 — "We are KISSing the review system" (Trust, Verify, Monitor). Now in rules/workflow.md (native `feedback_review_trust_verify_monitor`; [source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md))
> pinned 2026-10-28 — Diminishing-returns bar: option B, schema fields, fixed in advance, same every round; fresh blockers at round 3 mean redesign. Principle now in rules/workflow.md; detail in skills/gaze/references/panel.md ([source](../journal/2026/2026-10-28-diminishing-returns-bar.md))
> pinned 2026-10-21 — "No second order guards. Guards management is test doctor (pulse) work only." Now in rules/workflow.md (native `feedback_no_second_order_guards`)
> pinned 2026-10-09 — "guards on guards; doctrine is to remove" ([source](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md)); 2026-10-13 "Doctrine: simplify / remove the guard" ([source](../journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md)). Now in rules/workflow.md
> pinned 2026-10-27 — "REMOVE WORDING PINS" ([source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md))
> pinned 2026-10-27 — Escalation forks reversible options, capped at 5 minutes; calls by right are never forked. Now in rules/workflow.md ([source](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md))
> pinned 2026-10-21 — Ask up first, every time: "Sonnet resists my 'Ask up first' instruction". Now in rules/workflow.md (native `feedback_dont_idle_on_background`)
> pinned 2026-10-26 — Night mode: "Not to me, it goes to Fable for finishing. You are in night mode autonomous." Partly in rules/workflow.md — but see open question on the note's stronger wording (native `feedback_dont_idle_on_background`)
> pinned 2026-10-29 — Peer-relayed reversible ruling: "accept, don't barrier my work" (native `feedback_peer_relayed_rulings`)
> pinned 2026-10-31 — Cross-family gate removed: model and access are distinct, no field assumed known; "the cross-family benefit is unmeasured" (measured after: confounded); "Une bonne barrière est une barrière supprimée." `--require-cross-family` gone (PR 2085); family is a routing preference in skills/route/references/decorrelation.md ([source](../journal/2026/2026-10-31-cross-family-gate-dropped.md))
> pinned 2026-11-01 — "the ticket store is the inter-project channel"; the author kept ticket 1126 (comment-only hunks never block on scope) against the 1408 reversal. Now in rules/guards.md and rules/workflow.md § Cross-project work ([sources](../journal/2026/2026-11-01-ruleset-review-and-diet.md), [t1409](../journal/2026/2026-11-01-t1409-cross-repo-handoff-dissent.md))

Work shape:

> pinned 2026-10-03 — "a purely administrative tracker can go when there is only one operational task left. In fact the tracker should be the crowning delivery task." ([source](../journal/2026/2026-10-03-tracker-closure-pass-0205.md))
> pinned 2026-10-11 — No `/compact` before roar: it drops the detail capture records ([source](../journal/2026/2026-10-11-roar-clear-verdict-survey.md))
> pinned 2026-10-11 — "Ticketwork is automerge" (native `feedback_ticketwork_automerge`)
> pinned 2026-10-29 — "I don't want wait tickets. Doctors use their journal notes." Claim B ("a reminder is an open Blocked-by ticket") withdrawn by the author 2026-11-01 (ticket 1374) (native `feedback_no_wait_tickets`)
> pinned 2026-10-19 — "PRs are not waiting points; the existing ticket carries the follow-up." ([1466](../journal/2026/2026-10-19-smart-testing-1466-wrap-up.md))
> pinned 2026-10-28 — "I don't want a ticket sitting in line. I want a tool in the doctor's kit, ready to be used." (native `feedback_doctor_kit_tools`)
> pinned 2026-10-21 — "you end turn and block"; "Are you working or waiting?" (native `feedback_dont_idle_on_background`)
> pinned 2026-10-21 — "I AM NOT YOUR WAITER", "stop that 15mn wait, it is worse". Bounded waits now in rules/coding-bash.md (native `feedback_no_blocking_waits`)
> pinned 2026-10-09 — "on veut pas que le delta !": full table, delta above it. Now in skills/dashboard (native `feedback_delta_format`)
> pinned 2026-10-21 — Pi is not a second-class citizen: design for Claude Code, Codex and Pi together (native `feedback_pi_is_first_class`)
> pinned 2026-10-20 — "words stay dragon-themed, usage not a problem"; only user-facing skills get draconic names; rename only when the name misleads (smelt, 2026-10-29) (native `feedback_dragon_skill_names`)
> pinned 2026-10-29 — Faster gaze orchestrator: try it once the arena is up, by an arena arm, not by judgment (native `project_faster_gaze_orchestrator`)

Access, authority and workspace:

> pinned 2026-11-01 — "worktrees isolate the agents, so the primary checkout is the author's workspace"; branches stay for logical isolation; "Every fortification needs a backdoor": trivial changes may go straight to main. Now in rules/git.md § Branch and commit (ticket 1372 closed, PR 2129) ([source](../journal/2026/2026-11-01-author-workspace-rule-1372.md))
> pinned 2026-10-31 — Data locations: one store under the "our data" folder, declared per host by lifecycle (`DATASETS_DIR`, `MIRRORS_DIR`), ticket 1391 ([source](../journal/2026/2026-10-31-monitoring-and-data-locations.md))
> pinned 2026-10-23 — “Je disable le bloquage automatique des envois vers Claude, Codex et OpenRouter”; “Modifie les réglages du bloquage, mémorise et commite.” Now in scripts/on-start-context.sh ([source](../journal/2026/2026-10-23-model-transmission-authorization.md))
> pinned 2026-10-27 — Ticket 1196 option 1: agent sessions use the narrow PAT; GitHub settings are the author's acts (native `feedback_gh_admin_delegated`)
> pinned 2026-10-27, revisit 2026-11-03 — Main guard in enforce on padme and doudou; the author closed 1180 early "and asked to remember the watch instead" (native `project_main_guard_enforce`)
> pinned 2026-10-27 — Held tickets: 1243 "no encryption, no retrospective, no blocking; monitoring optional"; 1285 exposure accepted; 1164 measured instead of hooked ([source](../journal/2026/2026-10-27-session-close-held-tickets.md))

Case decisions with that PR as scope only (no precedent): PR 1633 merged without a third gate verdict ([source](../journal/2026/2026-10-26-pr1633-merge-on-author-authority.md)); earlier waivers and overrides: [raids](raid-review-and-merge.md).

Stated intent, not ruled (input for 1350): user memory apart from project memory; host memory local; tasks live in the agendas; agents need facts, not just preferences ([source](../journal/2026/2026-10-30-rulings-and-memory-design-input.md)).

## Hazards

- A waiver or merge instruction scopes one PR; it grants no future authority.

## Open questions

- Exposed contradiction, unsettled: native note `feedback_dont_idle_on_background` has description line "ask the top model (Fable) before EVERY author decision, even ones that look like the author's by right" (its 2026-11-01 body update scopes author-by-right calls to wait, matching the rule) against rules/workflow.md § Escalation protocol ("The author's calls by right ... are never branched or delegated; they wait"). Ticket 1439.
- Ex-post coder/reviewer health read awaits the author ([source](../journal/2026/2026-10-28-diminishing-returns-bar.md)).

## Retired

- "I trust you to admin my GH, yes" (2026-10-21): superseded by the author's choice of ticket 1196 option 1, 2026-10-27.
- Legacy advice to derive rules from consolidation: retired by the author's 2026-10-01 RETIRE LEGACY direction (memory/feedback_rules_come_from_memory_consolidation.md).
- "Editing prose is on main" versus rules/git.md main-read-only (ticket 1372): resolved by the author's 2026-11-01 ruling — the primary checkout is the author's workspace, now in rules/git.md (PR 2129); the native note `feedback_prose_edits_are_on_main` was updated to match. Ticket 1372 closed.
- "No wait tickets" versus "a reminder is an open Blocked-by ticket" (ticket 1374): claim B withdrawn by the author 2026-11-01; ticket closed.

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- Journal: all `../journal/2026/` links above.
- Native notes (Claude Code, harness store, read 2026-11-01), base path `~/.claude/projects/-home-haduong--agents/memory/`: feedback_rules_are_law_memory_is_decree, feedback_review_trust_verify_monitor, feedback_no_second_order_guards, feedback_dont_idle_on_background, feedback_peer_relayed_rulings, feedback_ticketwork_automerge, feedback_no_wait_tickets, feedback_doctor_kit_tools, feedback_no_blocking_waits, feedback_delta_format, feedback_pi_is_first_class, feedback_dragon_skill_names, project_faster_gaze_orchestrator, feedback_gh_admin_delegated, project_main_guard_enforce, feedback_prose_edits_are_on_main, project_government_memo_cooldown. Text of notes used this run: [sixth-smelt annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).
- Tickets: tickets/1349, 1351, 1369, 1372, 1373, 1374, 1439.

## Fallback
