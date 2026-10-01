# Memory v8 design and project boundaries

The author replaced the v7 library/compiler/embedding plan with repository
Markdown shared across Claude, Codex, pi and Vibe. The v8 design and delivery
plan were rewritten; superseded planning tickets were deferred without claiming
implementation. PR [1093](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1093)
merged after an independent Astra review requested as “simple, portable, efficace”.

The author then prohibited project outputs in the installed harness and
unsolicited rule proposals. Active roar, dream and memory-sweep instructions
still contained shared-store writes and promotions. PR
[1096](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1096)
removed those instructions and deferred crystallisation ticket 0925.
Astra identified a cleanup conflict: roar could add a capture commit after its
initial ancestry check and then treat that old check as permission to remove
the worktree. The procedure was changed to verify the current HEAD after capture
and preserve unintegrated work. The author requested at most one roar branch
and one bundled PR for tickets, documentation and factual capture, with
fast-track auto-merge after required checks.

The author replaced scheduled dreaming with a concluding lair suggestion after
five unprocessed experiences. Lair finishes without asking, waiting or invoking
dream. DREAM performs pruning, merging and refreshing of consolidated memory;
it checks coherence among indexed memories and applicable harness rules without
editing those rules. MEMORY.md has a strict maximum of 100 lines. The raw
journal remains append-only. PR
[1097](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1097)
merged after Astra review; parallel STATE/ROADMAP changes caused rebase conflicts
and were retained during resolution.

Verification included a full 1291-passing suite with three skips before the
later instruction refinements, adherence checks on those refinements, and green
forge checks. No runtime pilot or timer was deployed. Implementation tickets
0911, 0917, 0920 and 0988 remain open.
