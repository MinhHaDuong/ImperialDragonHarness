---
name: menagerie-build-state-2026-09-06
description: "Where the 0029 Menagerie program stands after the 2026-09-06/07 night run; what landed, what is blocked on which fact, and the eight questions waiting on the author"
metadata:
  node_type: memory
  type: project
  originSessionId: a690b729-abc6-4ef5-a712-f0be4683c51b
  modified: 2026-09-07T05:12:38.759Z
---

Session "Reimagining the Menagerie", 2026-09-06 into 2026-09-07. Main ended at 7a65d96, green (1274 passed, 15 skipped), zero open PRs.

**Read ticket 0029's log entry stamped 2026-09-07T05:10Z first.** It is the closeout state written for exactly this purpose and it supersedes any summary.

**Landed that night**: #409 the 281-question bank, #430 the ruled R34 predicate in the gate, #431 ticket 0734's cost and reply shape, #432 ticket 0733's cell counts and proposed floor of 12, #433 the embedder in the bench run identity, #434 and #437 blocker records, #435 the red-state exercise, #436 the passage-length distribution.

**This repo has no CI.** No `.github/workflows/`, so `gh pr checks` reports nothing and a poll written as `until gh pr checks N; do sleep; done` spins forever on a missing check and on a failing one alike. The gate is `make check` / `make lint` / `erg check`, run locally.

**The official score is structurally zero and that is correct.** No hit carries a page; `chunker.ts:8` collapses whitespace including Zotero's form-feed page break before any chunk exists, `ChunkRecord` has no field, the `passages` DDL has no column. `make golden` therefore fails by design and is deliberately not in `make check`. Ceiling measured: even a perfect page reader tops out at 85/195, because 110 of the 195 scored pairs carry no printed page on any alternate; a form-feed ordinal reader would reach only 15/195. Ticket 0734 owns this; a side table under `CREATE TABLE IF NOT EXISTS` carries the page without a stamp bump, but no migration rung can backfill it — the boundary was destroyed before the row existed.

**One predicate, one home.** `redstate.py` had grown a private copy of the ruled predicate; that copy was the entire accommodating 75-versus-51 gap (22 questions from substituting character spans for pages, 2 from a snippet locator, 0 from a looser work half that fired on nothing). It now reads the gate's report and computes nothing. Apply the same rule to any new bench tool.

**Blocked on one machine fact**: padme has no Zotero serving 23119 (probed read-only; the control is that the same probes on doudou return a listening socket and the `zotero` comms). That blocks 0732's paired re-run, 0700 entirely, and closeout items 3 and 4. Never touch doudou's Zotero or port 23119 — a peer session verifies a plugin in that profile.

**Eight questions wait on the author**, all listed in that 05:10Z log entry, none answered by an agent. The two with the largest consequence: whether the 85/195 official ceiling is the intended shape, and whether character spans may stand in for pages on the 99 of 202 pageless rows.

**How to apply:** resume from ticket 0029's log tail and DECISIONS.md, never from a conversation summary; check origin for open PRs before launching anything. Related: [[feedback-erg-log-stamp-must-match-wall-clock]], [[feedback-probe-needs-discriminating-control]].
