---
date: 2026-10-30
kind: episode
project: .agents
refs: [PR 2015, PR 2016, PR 2017, PR 2018, PR 2019, PR 2020, PR 2022, PR 2023, ticket 1349, ticket 1355, ticket 1358, ticket 1360, ticket 1361, ticket 1362, ticket 1363]
---

# Raid d2253c: seat evidence, landing refs, consumer hook report

Context: `/raid all open`, started 2026-10-29 while raid 29bf18's last PR (2013) was in review. Imagine and Plan were folded into one Sonnet 5.5 agent per ticket writing into its own ticket file; blind spot (Opus 5.5) and feasibility (Haiku 5.5) ran as one parallel pass. Executors were Sonnet 5.5 coder subagents.

Events:
- Excluded at selection: 1354 (needs-human), 1350 and 1351 (blocked), 1357 (in flight). 1346 was pulled at Imagine: its census child 1353 is closed and its trial child 1354 waits on the author.
- Blind spot measured the journal at about 1.1 MB on disk (about 275k tokens, derived at 4 bytes per token); the 1349 executor measured 708 KB of linked episodes, 9-202 KB per topic, and wrote the rebuild as per-department.
- Executors' own gaze runs on 1360 and 1362 recorded no cross-family seat (1362: `seats: self-only`). Gaze runs launched from the orchestrating session ran headless codex seats (gpt-6.1-sol, gpt-6-luna) on 2016, 2017 and 2019.
- 1355: the executor reported criterion 2 unchecked because `~/DOIfetch` was absent; verify-gate returned REROLL, naming `/home/haduong/CNRS/code/DOIfetch`. The read-only check there (hook_installed() False, no reference-transaction hook) cleared round 2.
- 1363 did not reproduce: two real `gaze_seat.py` codex launches read a git review tree under `-s read-only`; codex refuses a non-git directory. 1361's executor could not find the raw DOIfetch PR #33 seat report; the hollow-seat rule was tested on constructed fixtures only.
- 2016 was refused once at landing for a non-canonical `Ticket: refs ...` body line; reworded and landed.
- 1358 replaces the 0953 contract's FAIL with a visible skip when no adherence runner is declared; merged on the ticket's wording under the author's standing instruction not to hold work.

Outcome: PRs 2016-2020, 2022, 2023 merged; tickets 1355, 1358, 1360, 1361, 1362, 1363 closed; 1349 open for criterion 2 (a real rebuild accepted by the author); 1346 open as a tracker.
