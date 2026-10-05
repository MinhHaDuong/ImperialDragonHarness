---
name: coaching
description: "Replay the frozen, already merged PR benchmark board through a contained reviewer seat and report read-only ground-truth diagnostics."
argument-hint: "<model> [--endpoint URL] [--board FILE] [--credential-env NAME]"
---

# Coaching: cold replay

Run `skills/coaching/replay.sh <model>` for the shipped board. See
`references/replay.md` for options and result semantics. An optional
`--board FILE` selects a controlled fixture. The replay invokes the contained
`seat-runner.sh` once per board PR and prints a result only after every PR has
completed with a valid summary. Treat any nonzero exit as an incomplete replay.

This skill reads the board and already merged repository revisions. It does not
log trial tickets, change a reviewer roster, or make a promotion decision.
