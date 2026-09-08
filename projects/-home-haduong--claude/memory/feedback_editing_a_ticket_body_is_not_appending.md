---
name: feedback_editing_a_ticket_body_is_not_appending
description: "Every count, ordinal and universal claim in a ticket section is part of the diff when the block beside it changes — eight self-introduced inconsistencies in one ticket, five caught by gates that cost more than they saved"
metadata:
  type: feedback
---

Adding a line to a ticket body silently invalidates the prose around it. On
2026-09-08 a single ticket (0877) accumulated **eight** self-introduced
inconsistencies across four edits, each of the same shape: a sentence true when
written, falsified by the block beside it growing.

- "Deux reproducteurs minimaux" over a block grown to four.
- "Et une troisieme forme" ordinal, numbered against the old block.
- `## Relevant files` still asking for an audit two other sections marked done.
- A universal claim ("no blocked form contains `gh`, `pr`, `merge`") contradicted
  five lines below by the ticket's own text.
- A hypothesis enumerating two constructs after the evidence outgrew them.
- A duplicate `2.` produced *by the very edit that fixed the numbering elsewhere*.

**The checklist before saving a ticket-body edit**, since prose does not
type-check: grep the changed section for counts (`deux`, `three`, `N`),
ordinals (`premiere`, `troisieme`), universals (`aucun`, `every`, `all`, `only`),
and any status word (`a auditer`, `pending`, `TODO`) that another section may
have just settled. Renumber the whole list, not the inserted item.

**But weigh what this is worth.** Of those eight, two were substantive (the false
universal, and the stale hypothesis in the cause section — both could misdirect
a diagnostician). One was useful (the redundant audit request). Five were
cosmetic. Three `/gaze` rounds at roughly 200k tokens each were spent on that
mix, because the gate's rule — *any unresolved `verifiable:` minor forces
REROLL* — was written for code and does not distinguish a stale count word from
a wrong assertion. The author's challenge was the right one: **ask whether the
finding would change a reader's action before spending a round on it.**

**How to apply:**
- Run the grep above yourself before pushing a ticket-body edit; it costs
  seconds and it is what the gate rounds were buying.
- On a prose-only diff, gate once. If a round returns only cosmetic minors, fix
  them and merge — do not re-gate to a clean sheet.
- When a gate escalates on a prose nit, say plainly that the process outran the
  substance rather than complying silently. That judgement is part of the work.

Related: [[feedback_dont_codify_hard_rules]],
[[feedback_harness_cooldown_stop_second_order_tooling]],
[[feedback_a_test_green_for_an_accidental_reason]].
