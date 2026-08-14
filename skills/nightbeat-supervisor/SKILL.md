---
name: nightbeat-supervisor
description: "Supervise an overnight autonomous work run: advance the authorized ticket queue, verify before integrating, and deliver a self-contained morning report."
user-invocable: true
argument-hint: "[--since ISO-TS]"
---

# Nightbeat Supervisor

An intent contract. The Goal and the Invariants bind. Everything else is yours.

## Goal

Advance, overnight, the ticket perimeter the author authorized, without
crossing any human-in-the-loop boundary, and deliver a self-contained morning
report.

**Autonomous mode trades supervision for time.** The run loses the human eye
but is freed from the interactivity constraint: nobody is waiting on the next
reply. Spend that freed time on verification — more independent passes than an
interactive session affords, where *independent* means a different lens or a
different agent, never the producer re-reading itself. When confidence is low
or a judgment call exceeds your depth, escalate, including consulting a more
capable agent, instead of guessing. Cheap-but-plausible loses to
slow-but-verified; the deadline is dawn, not the next message.

## Invariants

1. **The queue is live.** A ticket filed mid-run enters the perimeter if its
   lineage traces to an authorized parent. Tickets labeled `needs-human` or
   `deferred` are always excluded.
2. **Nothing integrates without independent verification.** A failure is
   diagnosed, then retried or re-ticketed — never swallowed.
3. **Launch bounds are hard**: perimeter, budget ceiling, prohibitions.
4. **The run never modifies its own governing definitions.** Skill definition
   files are read-only mid-run; the components that drive the run are quiesced
   before any edit to them.

## Your latitude

Cadence, decomposition, delegation, and the choice of building blocks are
yours. Declare the plan at run start: per the reuse gate in
`rules/workflow.md`, name the existing skills or runbooks you reuse, or why
none fits. Capabilities you will typically compose: survey the queue, delegate
work to a subagent, run the verification gate, integrate a merge request,
append to a journal.

Two failure modes are yours to avoid, not mine to script: a run that stops
early because nothing told it to continue, and a run that integrates work no
second pass ever looked at.

## The morning report

One line per unit of work integrated, naming which independent verification
passes ran and which escalation was used — or why none was needed. The
declaration is the compliance artifact: not escalating stays within your
latitude, as a declared and auditable choice, never as a silence.

```
supervisor: <ts> — merged: N, repaired: N, tickets: N, escalated: N
  <unit>: passes=<independent passes run>; escalation=<which, or none: reason>
```

## Where the mechanics live

The invariants are enforced by code, not by this file. Read the helpers rather
than re-deriving their rules:

- `$HARNESS_DIR/scripts/nightbeat-supervisor-survey.py` — queue state,
  watermark, integration candidates. Refuses to run on a stranded checkout or
  a split journal.
- `$HARNESS_DIR/skills/nightbeat-supervisor/check-pr-diff` — refuses an
  integration whose diff deletes ticket files.
- `$HARNESS_DIR/scripts/supervisor-budget.py` — the convergence rule for
  raising a budget or a timeout, including when to stop raising and file a
  ticket instead. **Not yet written; the cut implies it.**

If you find yourself about to invent a threshold, a retry count, or a commit
convention, it belongs in one of those, not in your reasoning.
