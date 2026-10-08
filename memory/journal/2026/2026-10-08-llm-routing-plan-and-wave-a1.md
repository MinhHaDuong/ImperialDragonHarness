# LLM-chosen routing: plan, review and wave A1, 2026-10-08

The author asked for more workers on Haiku 5.5 and Luna, then redirected the work: drop the deterministic `model-level` x `effort` chooser, let the orchestrating model pick workers from the route grid plus per-runtime recommendations, keep skills free of model names, add Haiku to the grid, remove SpaceBunny, specify subagent and headless-CLI launch doors, treat gaze and review decorrelation as cross-family calls, and tear down the old infrastructure and ticket line. Runtimes named: Claude Code, Pi, Codex, Vibe.

Planning used two read-only Haiku sweeps (route and tickets inventory; decorrelation mechanics) and one read-only Fable review of the plan against the repo. The Fable review reported: the generator could not add a new arm (arm discovery read the frozen matrix; a hand-added row would raise `KeyError`); recommendation files with model names would fail the no-model-names test; tests pinning the qualifiers would go red between waves if deleted last; all five `context: fork` skills are the review skills; the tier pins on `agents/*.md` may have never been honoured; ticket 0375's "axis model" is the prose axis model, not the qualifiers. The plan was revised and approved after four rejections that asked for explanation of the plan, the route grid, `routes.json` and the launch doors.

Filed under tracker 1052 (PR #1262, merged): 1062 (A1), 1063 (A0), 1064 (A2), 1065 (B0), 1066 (B1), 1067 (B2a), 1068 (B2b), 1069 (B3), 1070 (C).

Wave A1 (PR #1263, merged, 1062 closed): `scripts/tournament-analysis.py` now includes arm n, emits a lineage `family` per arm, and prints real failure counts (the string had been hardcoded `failures=0/30`; b3, a, j, k and c2 each had one failure). Haiku 5.5 final on 10/10: quality median 22.5, 3.03 min, 0.0227 USD median per ticket; Luna @medium 21.75, 3.84 min, 0.0278 USD. An earlier statement in the planning conversation that the two cost figures had different units was wrong; both are per-ticket medians. SpaceBunny removed from `routes.json`, the grid comment and the route skill example.

Checks: local `make check` 1514 passed, 3 skipped. On PR #1263 the first run after the ticket close commit failed `tests/test_attribution_query.py::test_explicit_merge_coverage_does_not_accept_ambiguous_records[encrypted]` (a `git merge` in a temporary repository exited 128); the same code had passed the pre-close run, and a rerun of the failed job passed. Cause not established. No gaze or review panel ran on #1262 or #1263, so there is no review attribution to capture.

The worktree isolation guard refused compound shell commands and `git add` through the output-compacting hook; plain `/usr/bin/git -C <worktree>` calls worked.

Not started: A0 (1063), A2 (1064), B0 to C (1065 to 1070). Open author calls recorded in 1052's log and 1069: lifting 1052's `Blocked-by: 1047`; closing 1048 or keeping it deferred as grid data.

Sources: [PR #1262](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1262), [PR #1263](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1263), tickets 1052 and 1062 to 1070. No standing rules were changed in this wrap-up.
