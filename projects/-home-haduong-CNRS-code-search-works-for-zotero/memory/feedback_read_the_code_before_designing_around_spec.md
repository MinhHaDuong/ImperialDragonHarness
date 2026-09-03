---
name: read-the-code-before-designing-around-spec
description: "SPEC.md describes intended design, not shipped behaviour; check README's delivered column and grep the fork before writing tickets, briefs or rulings about a mechanism's constants."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a8c6145f-64b2-419c-8047-79b39ec71352
  modified: 2026-09-03T10:29:32.378Z
---

SPEC.md is a design document for what this repo intends to ship, and its
sections read exactly like descriptions of running code. On 2026-09-03 three
tickets (0590, 0607, 0608) and a decision brief were written about §5.2.6's
keyword refetch ladder — its pool constant, its one deeper retry, its R18
give-up — before anyone opened the source. None of it exists: `keywordSearch()`
issues one MATCH and returns, the pool is `limit * 3` rather than
`max(8×limit, 256)`, there is no 4 096 and no retry, and the keyword path takes
no scope parameter at all (`QueryOptions` is `{limit, mode}`). The
oversample-and-verify shape §5.2.6 describes is real but sits on the *vector*
arm. The author caught it in one question — "are we doing a query + 1 retry?" —
after the brief had already recommended raising a constant that is not there.

**Why:** nothing in the repo was wrong. README.md's standing table already
carried R5 `delivered=partial` and R18 `delivered=none`, which is precisely the
fact needed, and it was never consulted. The failure is reading a MUST clause
and a section full of numbers as evidence of behaviour — in a repo whose whole
method is to specify first, that inference is always available and usually
wrong. Same family as [[verify-the-load-bearing-claim]]: the sentence an outside
reader checks first was the one nobody ran.

**How to apply:** before writing a ticket action, a brief, or a ruling that
turns on a mechanism's constants, spend two minutes: read the requirement's row
in README.md's standing table (`delivered` = none / partial / both), then grep
the fork for the constant itself. Code lives in the untracked `fork/` checkout
— see [[search-the-fork-before-claiming-absence]]. If the mechanism is unbuilt,
say so in the ticket: the design question stays worth ruling (it is cheaper to
rule before implementation than after), but a *measurement* action against an
unbuilt path is a blocker that must be named, not a schedulable step. 0590's
action 2 planned to run query arms through a two-action path that does not
exist on the query surface, and 0605 had separately found the index stores no
collection or tag membership — two halves of the same missing thing, neither
noticed until the code was read.
