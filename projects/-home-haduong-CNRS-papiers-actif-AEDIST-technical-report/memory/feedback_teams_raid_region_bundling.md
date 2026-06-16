---
name: feedback_teams_raid_region_bundling
description: "Large prose-edit wave via Teams — sweeps-first, bundle tickets by manuscript region (one PR per section), red-team at end"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

Executing a large manuscript-edit wave (many tickets) via the Teams worker pool works well with this structure:

1. **Sweeps first.** Whole-file renames/policies (terminology, a caption/code policy) land BEFORE region edits, so later prose uses the final vocabulary. Encode as worklist `blockedBy` (or just merge them first). Run the sweeps as their own workers; they edit the whole file so merge them sequentially with rebase (low textual overlap → clean).
2. **Bundle tickets BY MANUSCRIPT REGION, not one-ticket-one-worker.** One worker / one PR per section or figure-group (e.g. "§5 bundle: 0612+0613+0614", "FIGCAPS: 0616+0617+0623+0625"), with multiple `**Ticket:**` lines. Each worker owns DISJOINT lines, so parallel worktrees rebase cleanly and you stay under the 8-agent cap. One-ticket-one-worker on the same section causes needless intra-region rebase conflicts.
3. **Emitter/.py and slides tickets merge freely** (different files from main.tex) — run them in the same wave as prose with no conflict.
4. **Gate-merge in dependency/region order**, rebasing each (see [[feedback_shell_timeout_no_loops]] for the bounded-merge discipline). Hold the most invasive PR (e.g. an appendix restructure) for LAST so smaller edits rebase onto stable text, not the monster.
5. **Interactive/decision tickets** (engineering, editorial calls) are held out of the autonomous waves; run their investigations via read-only workers, bring the author decisions, then execute.
6. **Red-team integration pass at the end** — tiered verifiers (haiku mechanical / sonnet structural / opus judgment), refute-by-default, against post-merge main. This caught nothing this time precisely because each ticket shipped a negative guard + green CI; it is still the gate that closes the tracker.

**Why:** 2026-06-15 reading-3 wave — 36 tickets via Teams across sweeps + 3 waves; region-bundling collapsed ~22 prose edits into ~10 PRs with near-zero merge conflicts; red-team found zero defects. Watch-outs: workers inconsistently close their ticket in-branch (handle both — erg-pr-merge for still-open, plain merge for closed-in-diff); and branch-allocated erg IDs collide when a prior ID is still in an unmerged PR ([[feedback_erg_id_collision]]).
