---
name: feedback-silent-ceiling-class
description: A cap that announces completion is worse than one that fails — found five times in one codebase in a day; probe the boundary, don't read the status
metadata:
  type: feedback
---

Reviewing a search tool on 2026-08-21 turned up **five independent limits in one
day, every one of them silent**: a hardcoded 5 000-item cap whose status
reported `5000/5000 done` on a 7 540-item library; a 40 000-char/item default
that discarded 59% of the text; a serialisation ceiling that threw into a
`logger.warn` while the build reported `done` over a stale file; a heap ceiling
that made the written index unreadable; and a rebuild-only index that never
noticed an added or deleted document.

**Why:** each one converts a *coverage* failure into what reads as a *negative
result*. A truncated index answers "nothing found" with exactly the confidence
of a genuine miss, so the tool's most useful output — "there is nothing on X" —
becomes the one you cannot trust. Ranking degrades gracefully; coverage does
not. The author's image: it is not a quality trade-off, it is discarding the
last volumes of a dictionary.

**How to apply:** when auditing any index, cache, or paginated fetch, do not
read the status object — **probe the boundary**. Compare what the tool reports
against what the source actually holds (`Total-Results`, a row count, a file
count), and check the round trip, not just the write: the read path can fail
earlier than the write path, and here it did. Every one of these was found by
measuring against ground truth, none by reading a log. Same rule as
`tickets/AGENTS.md` on forge queries — a check whose all-clear is
indistinguishable from "I could not look" is not a check.

Corollary that made the upstream report land well: state the measurement, not
the verdict. "Storing in one string does not scale" is a judgement on the
maintainer; "5.4 GB resident and OOM on reload for a 7 500-item library, here is
the reproduction" is a fact he can check.

Related: [[project-zoteus-fts5]]
