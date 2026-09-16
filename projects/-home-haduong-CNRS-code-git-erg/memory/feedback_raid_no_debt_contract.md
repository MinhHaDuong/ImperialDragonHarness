---
name: feedback_raid_no_debt_contract
description: "Operating contract for raids in this repo — MOE arbitration, no invented work, consult Fable on doubt, and a ticket opened is a ticket closed in the same run."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a27d6179-c527-421f-a14a-e4de26d3f494
  modified: 2026-09-16T15:32:39.622Z
---

The author's standing contract for a raid here, set 2026-09-16:

> *"Mode MOE, sans inventer de travail que le client n'a pas demandé, en
> consultant Fable si tu as un doute, et si tu ouvre un ticket c'est pour le
> traiter dans la foulée. NO DEBT."*

and later, when the queue was nearly empty:

> *"Reste en posture de MOE qui arbitre sévèrement contre tout ce qui sent le
> goldplating."*

**Why:** a raid's failure mode is minting tickets faster than it closes them.
This one was caught doing it mid-flight — *"on a ouvert 4 tickets pour en fermer
3"* — and again over-hardening a fix against a state no store was in (*"on
marche sur la tête non ?"*). Concurrency times the severity floor sets the
arrival rate; without the same-run rule, a raid converts one queue into a longer
one and calls it progress.

**How to apply:**

- Arbitration is the job, not a thing to escalate. *"Arbitrer c'est ton métier de
  MOE et si tu as des doutes, advisor Fable."* Decide; consult a peer model on
  genuine doubt; do not hand the call back up as a question.
- A finding below the severity floor (blocks a merge / corrupts state / bites the
  science) is fixed inline in the same PR, recorded, or dropped — never ticketed.
  The 2026-09-16 raid ended six tickets opened, two closed wontfix on audit,
  three deleted before landing in favour of one-line fixes, one merged.
- Reverse your own earlier acceptance when the measurement changes. The author's
  read-only 0444 proposal had been accepted that morning; a re-survey measured
  zero offending adopters, which turned it into a new failure path in `erg init`
  bought for nothing. Withdrawing it was right, and recording *why* in the ticket
  body — rather than deleting the section — is what stops it being reinvented.
- Say no to a defensive arm against a state no store is in. That is the concrete
  shape goldplating takes in this repo.

Related: [[feedback_no_meta_test_infrastructure]],
[[feedback_non_vacuity_is_per_case.md]].
