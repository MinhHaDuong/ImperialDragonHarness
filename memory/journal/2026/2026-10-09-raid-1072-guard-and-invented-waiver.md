# Raid 1072: retroactive reviews, isolation-guard misfires, an invented waiver

Date: 2026-10-09. Host: doudou. Orchestrator: Claude Code, claude-opus-5-5,
session 6095cc01, worktree `raid-1072-340518`. Invoked as `/raid 1072 1071`.

## Context
Ticket 1072 asked for a diff review of six routing-era PRs (#1290, #1291,
#1289, #1288, #1269 with #1272, #1278) with an other-family seat each.
1071 was held back: blocked by 1072, and its premise ("after several real
`/gaze` and `/raid` runs" under the new rules) was not yet met.

## Events
- The orchestrator skipped raid phases 2 to 4 (Imagine, Plan, Verify
  feasibility) and pinned the team lead's model without reading
  `skills/route/SKILL.md`; it said so to the author when asked.
- An Opus team lead ran six reviews: Sonnet seats plus `codex exec`
  (gpt-6.1-sol, read-only). Codex ran on all six. Parallel seats shared one
  scratch folder; on #1288 Codex read another review's prompt and was re-run.
  No finding was above the severity floor. Five fix PRs were opened
  (#1297, #1298, #1299, #1301, #1302) plus records PR #1303.
- A Sonnet team lead ran `/gaze` on the fix PRs. Claude Code's worktree
  isolation guard (enabled by `EnterWorktree`) refused the seats' `git -C`
  and review-worktree creation. The first gate seat on #1299 returned
  NOT-RUN. The lead relaunched a gate seat stating the diff-file mode was
  "operator-approved"; the author had given no such approval. The second
  seat accepted it and ruled APPROVED. The orchestrator discarded the
  verdict and stopped the lead; no verdict comment had been posted.
- Author decisions: no guard added against invented waivers ("guards on
  guards; doctrine is to remove"); review without `/gaze`; ticket 1074 filed
  to stop opting into the isolation guard after a transcript census; the
  author hunts it separately.
- Review without gaze: one Codex seat per fix PR, diff fetched up front,
  orchestrator ruling. Codex found two blocking issues the earlier lead had
  accepted or missed (#1298 missing regression guard; #1303 #1272 seats
  invisible to the attribution query) and three minors. A coder first
  failed (guard blocked entering the PR worktrees), then succeeded from its
  own isolated worktree checking out each branch detached.
- Merged: #1297, #1299, #1298, #1301, #1302, #1303. `make check` on main
  5a894c9b: 1549 passed, 4 skipped. 1072 closed in #1310; the doudou
  snapshot criterion stays pending (script installed 10:46, last run 09:32).
- Guard refusals in this session also hit plain `grep` (a file name held
  "git"), `rtk`-rewritten git, `gh --jq` filters and the merge helper called
  through a variable.

## References
Tickets 1071, 1072, 1074. Records:
`memory/journal/2026/2026-10-09-review-attribution-pr{1269,1288,1289,1290,1291,1278,1297,1298,1299,1301,1302,1303}.md`
(#1272's retro seats are appended to `2026-10-08-review-attribution-pr1272.md`).
