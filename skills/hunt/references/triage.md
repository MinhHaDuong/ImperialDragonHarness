# Hunt entry triage — who runs it, who skips

The Route step's triage runs **once**, at hunt entry, before any
code is written, and only in the author's live interactive session. This file
holds the justification for *why* the other callers skip it, so the hot path
need not restate it.

## Callers that skip straight to the Worktree step

- **An executor already running detached** — identified by the Worktree step's
  ownership check, which is the sole discriminator; do not restate its
  conditions. An executor spawned by an interactive hunt was triaged by that
  hunt before it was spawned, so re-reading the tells buys nothing.
- **An `inline` invocation** — the author passed `inline` explicitly to keep
  the co-working behaviour in their own session.
- **A headless run** (`claude -p "/hunt <id>"`) — already the detached case an
  orchestrator asked for.

Each skip is total, the needs-human branch included.

## Raid is not a second triage

A raid picks its own targets and no interactive hunt precedes them, but it does
not re-triage here: `erg ready` already skip-lists the `needs-human` label
(`tickets/.ergrc`), and raid Phase 1 screens its own targets.

## Argument shape

Arguments are `<ticket-id>` optionally followed by `inline`, so the ticket id
is the leading token of `$ARGUMENTS` — what every `t$ARGUMENTS` worktree name
and `${ERG:-tickets/erg} close $ARGUMENTS` substitution refers to.

## The Exit criteria step's already-met fast path never reaches triage

It executes nothing — it only lands a close through the normal PR flow — so it
needs no triage.
