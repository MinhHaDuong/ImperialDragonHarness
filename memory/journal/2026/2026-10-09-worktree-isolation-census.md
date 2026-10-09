# Worktree isolation guard census (ticket 1074)

Context: ticket 1074 proposed dropping the session `EnterWorktree` opt-in if
transcripts showed no true catch by Claude Code's isolation guard.

Observed (transcripts under ~/.claude/projects, 2026-10-09): 9,537 refusals in
tool results. By stated reason: rtk-wrapped git ~3,000; "too complex to
verify" ~3,200; `cd`/`-C` to the shared checkout 1,704, of which 154 matched a
git write verb. Of those 154, read one by one: about 145 false positives
(mostly `git worktree add/remove` of review trees from the primary); 3 clear
true catches (`git -C ~/.claude restore --worktree` over uncommitted memory,
twice, 2026-09-24; `git -C <primary> checkout <branch>`, 2026-09-06); 4
probable ones with cwd unrecorded.

Blind-spot pass (raid): `EnterWorktree` also moves the session cwd; plain
`git worktree add` leaves Edit/Write on the primary checkout.

Decisions (author): portability and lightening constraints; split into 1076
(skills drop `isolation: "worktree"` for a plain-git recipe with
`git worktree lock`, merged as PR #1313) and 1077 (session opt-in, after a
subagent-spawn and `$PPID`-lifetime experiment). Author stopped a Codex
cross-family seat for time and chose a Fable seat instead.
