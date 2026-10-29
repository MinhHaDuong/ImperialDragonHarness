# git in a worktree session

Scope: running git from inside a worktree session of this harness — which
guards refuse which command forms, and which remedy reaches which checkout.
Built from an attributed operational note (re-tested 2026-09-06) and
refreshed with the 2026-10-08 to 2026-10-13 journal; assess against the
current rules and host configuration before relying on any specific refusal
message.

## Supported observations

The source note distinguishes two independent guards, not one. The first is
the rtk rewrite: `git <verb>` is rewritten to `rtk git <verb>` before the guard
inspects it, and the refusal text says so; both `\git <verb>` and
`/usr/bin/git <verb>` defeat this one. The second is the containment rule
about redirecting git to the shared checkout via `-C`: neither escaped form
defeats it — only calls held in a script file reach another checkout. The note
reports that conflating the two guards is the trap, and that one deleted note
advised exactly the conflation (`\git -C <path>`) as its headline remedy.

Refresh, 2026-10-09 (ticket 1078, PR #1314): rtk 0.49.0 rewrote `add`,
`commit`, `push`, `fetch`, `worktree`, `branch`, `diff`, `show` and `git -C`,
and spared `status`, `log`, `switch`, `rev-parse`, `merge-base`.
`exclude_commands = ["^git\\b", "^make\\b.*\\bcheck\\b"]` was then set on
doudou and padme, and a ten-shape probe returned `No rewrite` for every git
shape, with `ls -la` still rewritten as the positive control. On those two
hosts the first guard therefore no longer fires on git since that date; it
still applies to other commands and to hosts without the exclusion. The
doudou config still carried the line on 2026-10-13 (read by the third dream).

The isolation guard itself kept refusing other shapes. A transcript census on
2026-10-09 counted 9,537 refusals: about 3,000 rtk-wrapped git, about 3,200
"too complex to verify", 1,704 `cd`/`-C` to the shared checkout. Of the 154 of
those that carried a git write verb, about 145 were false positives (mostly
`git worktree add/remove` of review trees), three were clear true catches
(`git -C ~/.claude restore --worktree` over uncommitted memory, twice on
2026-09-24; `git -C <primary> checkout <branch>`, 2026-09-06) and four were
probable. Counts are the census's own, read by hand, not re-measured here.
Refused shapes recorded in the period: compound `&&` chains containing git, a
heredoc whose text held the word "git", a command name held in a variable,
`gh --jq` filters, `grep` on a file name containing "git", and text that merely
quoted "rtk … git" (a PR body, an ssh string, one `!` command the author
typed). Each passed once split into plain commands or moved into a script
file. The third dream's own session saw the same classes: globs, loops and
`rtk hook check git …` were refused.

What the guard cost in review: `/gaze` seats and gate seats could not reach
review worktrees on PRs #1309, #1326, #1329, #1352, #1366 and the raid-1072
fix PRs (details in [raids, review panels and merges](raid-review-and-merge.md)).

## Author decisions recorded in the sources

Ticket 1074 (closed 2026-10-09) split the question: skills dropped
`isolation: "worktree"` for a plain-git recipe with `git worktree lock`
(ticket 1076, PR #1313); whether sessions keep opting in through
`EnterWorktree` was then ticket 1077 (closed 2026-10-14; see below). The census's
blind-spot pass noted that `EnterWorktree` also moves the session cwd, whereas
a plain `git worktree add` leaves Edit and Write on the primary checkout.

## Refresh: EnterWorktree retired (2026-10-14)

[Ticket 1077 / PR #1407](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md)
closed after controlled probes: plain worktree operations passed in an
un-entered session, whereas EnterWorktree enabled a guard refusing both
`-C` and `cd` into sibling trees, including for subagents. Plain operations
from the entered tree without `-C` still passed. A parallel session obtained
the same result. The author chose to drop EnterWorktree without a replacement
guard, keeping plain git worktrees. Current `rules/claude-code.md` forbids
EnterWorktree and specifies add/lock/cd; the earlier refusal catalogue is
historical and conditional on sessions that activated that runtime guard.

A restart reset cwd to the primary checkout and a relative edit reached main;
the edit was moved to the branch and reversed on main. After the change,
review-tree creation and reads succeeded from an un-entered session. The
accepted residual risk is loss of the runtime guard against writes aimed at
another tree. The concurrency topic records this same episode, not a separate
measurement of the risk.

## Refresh: refusals after 2026-10-14, collisions, allow rules

Two independent transcript scans place the guard refusals before the
retirement. A 14-day scan of 2,364 transcripts found about 1,270 worktree-guard
refusals, all on or before 2026-10-14, none after, with Bash volume above 2,000
calls a day ([velocity scan](../journal/2026/2026-10-21-velocity-scan-stale-baseline.md));
the premise check for tickets 1166 and 1168 found zero for 2026-10-15 to 10-21,
and the author closed both. A 28-day `trace-friction.py` read on padme counted
3,391 denials falling from about 750 a day to 0 in the last three days
([test-doctor rename](../journal/2026/2026-10-27-test-doctor-rename-1228.md)).
Both entries call this a timing match with the 2026-10-14 change, not an
isolated cause. The census figures above are therefore period figures.

Worktree-name collisions (ticket 1328, PR #1934): a subagent's shell starts in
the spawner's cwd, an unchained failed `git worktree add` let the following
`lock` lock the spawner's tree, and hunt's "owned already?" adopted a clean tree
handed by path. Earlier, hunt's `t$ID-$PPID` path equalled the raid
orchestrator's own worktree, which cleanup then removed, with no work lost. The
fix chains add, lock and echo, redraws the `$RANDOM` suffix, and limits adoption
to a path named in the brief; `rules/workflow.md` now names `{pid}` as
`$PPID-$RANDOM` ([b6aabf](../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md),
[1326](../journal/2026/2026-10-28-raid-f642df-1326-opt-out-not-refusal.md)).

The permission classifier refused rule-mandated `--force-with-lease` and branch
deletes twice in 24 h; with the author's permission, narrow allow rules were
added on padme and `scripts/claude-allow-check.py` checks them (ticket 1331,
PR #1943); `git update-ref -d` stays refused. This agrees with
`rules/claude-code.md` § Allow rules ([triage](../journal/2026/2026-10-29-harness-doctor-triage.md)).
A worktree that appeared mid-review with a pid-less lock was, per the entry,
"consistent with the headless seat following the session-start worktree rule",
cause not established ([yawn](../journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md)).

## Sources and exceptions

- [git in a worktree session](../reference_git_in_a_worktree_session.md) — attributed operational note, re-tested 2026-09-06; its rtk-on-git description predates the 2026-10-09 exclusion.
- [rtk git exclusion](../journal/2026/2026-10-09-rtk-git-exclusion.md)
- [Worktree isolation census](../journal/2026/2026-10-09-worktree-isolation-census.md)
- [Closing 1074: guard refusals](../journal/2026/2026-10-09-close-1074-guard-refusals.md)
- [Raid 1072 guard refusals](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md)
- [Tournament publication, refused compound commands](../journal/2026/2026-10-08-tournament-publication-wrapup.md)
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
