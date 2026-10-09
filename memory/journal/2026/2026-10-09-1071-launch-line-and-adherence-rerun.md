# 1071 follow-up: launch-line recount and adherence re-run (2026-10-09)

Continues [routing review round two](2026-10-09-routing-review-round-two.md).

## Observed
- Launch line counted only after its introduction (commit `de75ce05`, 2026-10-09T05:36:06Z): 1 of 35 launches carried a `worker | family | effort | risk row | reason` line; 0 of 87 before. The one hit was the `gpt-6.1-sol` seat launch. This session's own lines were written in chat and the counter found none, so the rate is a floor (counter needs five pipe-separated fields in the recorded text before the launch; Codex traces and the 9 headless matches were not checked).
- Ticket 1070 criterion 2, re-run twice by sub-agents on PR 212 (`e6907845`, base `a06cfe28`): run on the bare PR flagged `scripts/pretooluse-worktree-path-guard.sh:15` (the 0310 weak predicate) through the mechanical path with the rule text supplied by the caller, no worker launched. A fixture editing `.claude/rules/*.md` (copies of `rules/*.md`, added with `git add -f`) plus a `lint` target returned PASS, the violation unflagged, phase 3 judged applicable but no subagent spun. Filed as ticket 1080 (#1341).
- Transcript model ids for the 1071 raid, read from `"model"` fields: writer (coder) `claude-opus-5-5`; `/gaze` forks for #1338 and #1337 `claude-sonnet-5-5`. No verified effort level was found in the transcripts, and the #1338 review seat's id is not in the fork transcript.

## Pending capture
Review attribution records for #1337 and #1338 remain unwritten: the format requires effort, and the #1338 review seat's model id, neither of which the trail establishes.
