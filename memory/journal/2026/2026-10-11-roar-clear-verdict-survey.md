# Roar reorder and /clear verdict (PR #1354, ticket 1083)

Context: the author asked whether roar is a moment to compact or clear.

Observed in a transcript survey on padme (2026-10-11, 400 most recent
`~/.claude/projects/*/*.jsonl`): 59 sessions outside `.agents` and 5 inside ran
`/roar`. Context at `/roar` was typically ~200k outside `.agents`, ~100k inside;
about 20 roars ran above 256k (max 768k). About 22 of 59 sessions kept working
after roar on the same context, ending at up to 864k; one such tail reached an
auto-compact at 713k. No session ran `/clear` after a roar. Counts come from a
heuristic script (last usage line per session; user messages excluding task
notifications), not from a validated census.

Decisions: no `/compact` before roar (it drops the detail capture records);
capture moved to step 3 so recall precedes the sweep, steps 7–11 keep their
numbers; step 11 ends with a `/clear` verdict. A phase-B subagent for the
mechanical steps was discussed and not ticketed.

Review: `/gaze` round 1 REROLL. The red-team seat alone raised two blockers
(step 11's pending definition omitted pending capture and kept worktrees; step
9b made the armed bundle "pending", so the verdict could never fire); the gate
upheld both. Round 2 APPROVED at fda7ab12. All seats were reported by gaze as
"sonnet", same family as the writer; the verbatim model id is not exposed in
the review trail.

A first wording, "background agent", tripped `tests/test_launch_model_choice.py`
(fan-out regex) and was reworded before the PR.
