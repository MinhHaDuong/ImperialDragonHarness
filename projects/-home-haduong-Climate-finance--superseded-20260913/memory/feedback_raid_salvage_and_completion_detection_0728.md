---
name: feedback_raid_salvage_and_completion_detection_0728
description: "2026-07-28 raid (tickets 0570/0571/0625): session-limit kill survived by salvage-first + relaunched finishers; a monitor that never fired cost 80 idle minutes; pgrep matched a sibling worktree's make check; parallel make -j4 NJOBS=6 cut a divergence-check chain from hours to under one"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T18:12:52.788Z
---

Four operational lessons from running the three-ticket raid (0570, 0571,
0625) that landed as PRs #1269, #1279, #1280 on 2026-07-28.

**Salvage-first survives a session-limit kill.** Two executors were killed
mid-run by the session limit. Both were salvaged — the in-progress commits on
their branches were sound and complete-enough that a relaunched finisher
agent could pick up the branch and carry it to a mergeable PR rather than
restarting the ticket from scratch (PR #1269's body documents this
explicitly: three commits salvaged unchanged, one WIP commit reworded). The
pattern to reuse: on a session-limit kill, check the killed branch's log
before re-ticketing — a finisher continuing existing commits is far cheaper
than a fresh executor re-deriving the same work.

**A monitor that should fire on completion can silently not fire.** One
background step's completion monitor never triggered; the actual wake-up was
manual, costing roughly 80 idle minutes with nothing advancing. No root
cause was isolated in the moment (the monitor mechanism itself was not
instrumented to say why). Treat "the monitor will tell me" as unverified
until it has actually fired once in the session — a bare wall-clock check-in
is cheap insurance against a silent monitor.

**`pgrep`-based completion checks are unreliable across worktrees.** A
completion check that grepped the process table for a running `make check`
matched a *different* worktree's `make check` invocation, not the one being
waited on — a false "still running" (or the inverse false "done", depending
on which direction the match landed). Process-table matching cannot
distinguish which worktree a command is running in. Prefer tailing the
specific log file the target process writes to over matching on command
name/args in `ps`/`pgrep` — this generalizes the existing
`feedback_rtk_rewrites_grep_output` caution about trusting derived signals
over the artifact itself.

**Parallel `make -j4 NJOBS=6` collapsed a divergence-check chain.** A
byte-compare/divergence-check sequence that serially would have taken
4-6 hours completed in under one hour once run with `make -j4 NJOBS=6`
(four make-level jobs, six workers within each). Worth reaching for
whenever a raid step is a chain of otherwise-independent regenerate-and-
compare targets rather than assuming serial execution is the only safe
mode — the ticket 0625 network-limitations regeneration and the ticket 0570
Z-series regeneration were exactly this shape.

**The general defect class now has a tracking ticket.** "A document asserts
what the real data does not support" surfaced three times in one raid under
three different mechanisms — 0357's unresolved reference, 0570's resolved-
but-meaningless sentinel, 0651's synthetic-fallback figure (open) — with no
guard covering the general property. Filed as ticket 0652 at this wrap-up
(PR #1281, ticket-only fast path), asking for an explicit decision:
consolidate the three (four, with 0641's corpus-drift variant) per-mechanism
guards into one invariant, or keep them separate on stated reasoning.

Related: [[feedback_check_the_detector_first]],
[[feedback_rtk_rewrites_grep_output]],
[[feedback_corpus_rerun_byte_compare]].
