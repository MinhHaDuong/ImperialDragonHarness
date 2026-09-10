---
name: feedback_stale_forward_promises_in_skills
description: "Resident skill text that promises a future — until the…, not yet drafted, when converted — keeps reading as pending work after the decision behind it is settled, and agents act on it"
metadata:
  type: feedback
---

Three such promises sat in `skills/gaze/SKILL.md` at once (2026-09-10). Convergence
mode said "unchanged until the B-arm week flips it on" — the study was voided
2026-07-14. `/simplify` was "out of this ticket's scope … tracked at ticket 0349" —
0349 was closed wontfix the day it was filed. `/verify-wave` was "not yet drafted"
since 2026-04-17 and had no ticket at all.

**Why:** a skill body is loaded into every fork that runs it, so stale prose is not
inert documentation — it is live instruction. Asked to shorten gaze, a session read
the convergence sentence, took it for pending work, and recommended enabling a mode
its own author had cancelled two months earlier. Nothing links skill prose to ticket
state: closing a ticket wontfix never asks which skills still promise it.

**How to apply:** it is a periodic-inspection item, not a guard — the author declined
a systematic check (2026-09-10), so it lives as a sub-item of `/healthcheck` check 11
(docs freshness). Grep `skills/*/SKILL.md` and `rules/` for the prospective
constructions, then confront each with its ticket. Expect false positives: of eight
hits, five were legitimate runtime sequencing. Report, never auto-edit — deciding
that a promise is dead is the author's call. Related: [[feedback_tests_pinning_prompt_prose]]
(a test asserting a word appears in a skill file goes stale the same way),
[[feedback_measure_whether_a_guard_ever_fired]].
