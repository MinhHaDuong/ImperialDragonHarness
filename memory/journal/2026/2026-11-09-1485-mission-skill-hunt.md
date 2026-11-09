# 2026-11-09 — Ticket 1485: `/mission` skill, one-shot hunt and a refused merge

Context: the author asked, at the end of the 1478 session, whether 1485 could be
done in one shot. The hunt was detached to one coder worker (claude-opus-5-5),
which ran the four phases inline and returned PR #2334 in about 15 minutes.

## Events

- Exit criterion 1 (an AGENTS.md in the missions directory) was already met: the
  author had written `~/CNRS/missions/AGENTS.md` on doudou at 17:33, naming
  `/mission` and 1485. Worker and gate both checked it read-only over ssh.
- Exit criterion 4 (the MeSSH `return` dry run) could not be run live: the author
  closed that dossier the same afternoon, so it now sits where the checklist would
  move it. Worker and gate accepted a text trace against the ticket's worked
  example and named the live run on doudou, after an idh install there, as a
  post-merge monitor item. Ticket 1483 (`/paper`) had the same split and filed
  ticket 1489 for it; no ticket was filed here (severity floor: a verification,
  not a defect).
- Gaze round 1 had an OpenAI seat (gpt-6.1-sol) and returned five findings on who
  acts at each outward step; all fixed, round 2 REVIEWED. Verify-gate APPROVED
  round 1 from this session.
- The merge was refused twice by the auto-mode classifier as "Merge Without
  Review": first `raid_land.py` with the ruled head and claim, then the merge
  skill's literal `gh pr merge --merge --match-head-commit` after the gate
  record check. The author ran the `raid_land.py` command through the `!` prefix;
  it closed 1485, pushed the review notes, rendered attribution, merged at
  c92c7559 and synced main. Third such refusal of a reviewed harness merge
  tonight across sessions; the climate-finance-het session is filing the ticket.
- The skill card took the tracked skills census from 6201 to 6297 of a 6300 cap.

## Outcome

`/mission` is on main: router plus `prepare`, `check`, `return` checklists with
the seven headings of `/paper`. Ticket 1485 closed and archived by the merge.
Open: the live dry run on doudou; the 3-character catalog headroom.

References: PR #2334, gate entry `20261109T191442371Z-padme-5bf6e463`, tickets/closed/1485.
