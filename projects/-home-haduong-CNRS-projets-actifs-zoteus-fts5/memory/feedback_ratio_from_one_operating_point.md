---
name: feedback_ratio_from_one_operating_point
description: A speedup measured at one operating point is not a property of the system; check it at the point the design actually uses
metadata:
  type: feedback
---

A benchmark ratio is measured *somewhere*. Quoting it as a property of the
system assumes it holds everywhere the design will operate, and that assumption
is usually untested.

zoteus-fts5 ticket 0008 (2026-08-21): binary quantization measured **13x
faster and 24x smaller** than float32 at `k=30`. The ticket was filed on that
figure, and the number was reported to the author as free headroom. But the
two-stage design does not query at `k=30` — it needs a *pool*, and
`sqlite-vec`'s vec0 k-best cost grows faster than linearly in `k`: 7,7 ms at
k=30, 83,6 at k=480, 216,8 at k=960, against 121 ms for the entire exact
float32 scan. So the pool that preserved recall (16x, recall 0,998) cost
272 ms against a 110 ms exact scan — **slower than the thing it replaced**.
Shipped off by default.

A second instance the same day: a memory ratio (5 370 MB -> 121 MiB) compared
process RSS on one side against process RSS on the other, but SQLite uses
buffered I/O with no `mmap_size`, so kernel page cache holding a 949 MiB
database file is absent from its RSS while the JS heap figure has no such
hidden remainder. Same shape: a ratio whose two halves are not measured in
comparable conditions.

**The same shape with the sign reversed, 2026-08-22.** 0008's fixture verdict
was re-tested on 93 022 real embeddings. Recall at a 4x pool was **0,884 on
real data against 0,628 on the fixture** — the fixture was a *harder* problem
than reality, not a conservative stand-in for it, so reading its curve as a
lower bound had been safe by luck. The original ruling turned out narrow rather
than wrong: still true at the 16x pool it was measured at, false at 8x, where
the two-stage path is 1,65x faster at 0,953 recall. Four instances in one
chantier: 0008's k=30, 0011's "few hundred MB", 0005's two-point memory curve
read as flat, 0013's four-query ranking test.

**A fixture is not conservative by default.** It is a different distribution,
and which direction it errs in is an empirical question, not a safety property.
Say which one you measured on.

**Why:** the ratio is the most quotable artifact a benchmark produces, so it
travels furthest from the conditions that made it true — into tickets, status
documents, and upstream reports.

**How to apply:** before quoting a ratio, name the operating point and ask
whether the design runs there. Measure a *curve*, not a point, whenever the
parameter is one the implementation will vary. And check that both halves of
any comparison are measured the same way — an asymmetry in *kind* is worse than
an asymmetry in value. Related:
[[feedback_agent_reported_numbers_need_artifacts]],
[[feedback_invisible_bias_in_both_arms]].
