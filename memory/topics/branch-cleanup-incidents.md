# Branch-cleanup incidents

Scope: the incidents behind branch-cleanup practice in this harness. The
current rule is `rules/git.md` § Branch cleanup: `/roar` step 10 cleans only
the just-completed ticket's explicitly identified branches and full head OIDs,
keeps git's ordinary `-d` and worktree refusals, and leaves repository-wide
housekeeping to lair and molt (pinned by `tests/test_branch_cleanup_recipes.py`).
This topic records evidence; it does not restate or extend that rule.

## History: the loop era (ticket 0242)

The source note attributes one incident per guard of the earlier loop
recipes. An unguarded loop deleted local `main` during a hygiene pass
(2026-06-10), recovered by re-tracking `origin/main`. An unguarded remote
sweep hit the bare `origin` symref that `${ref#origin/}` does not strip,
aborted under `set -e` on its first iteration and left every stale branch in
place (2026-08-14). The note explains why those loops used `-D` inside an
ancestry probe (`-d` checks merged-into-HEAD, not merged-into-`origin/main`)
and keyed on exit status (rtk output rewriting before v0.45.0). That
description is superseded as current practice: `rules/git.md` no longer
inlines loops and its cleanup now keeps `-d` refusal and never forces. The
incidents stand.

## Supported observations: PR #1374 (2026-10-12 to 2026-10-13)

Ticket 1084 replaced roar's inline close-and-clean steps with a script. Round
2 of its review found the executor had swapped `git branch -D` for
`git update-ref -d`; measured directly, `git branch -D topic` refuses a branch
another worktree stands on, while `git update-ref -d refs/heads/topic <oid>`
returns 0 and removes it. Round 3 found three defects in the
delete-then-restore compensation: `core.abbrev=4` output that the parser could
not read, a tag named after the printed abbreviation restoring the wrong tip,
and an interruption window leaving a tip with no ref or reflog. Later rounds
found failed metadata reads compared as equal, a configured fetch refspec
overwriting foreign local refs, and git 2.53.0 crashing (SIGSEGV) on an empty
`branch.remote` override.

The author then narrowed scope (PR comment, 2026-10-13): roar cleans only the
current task's worktrees and branches, general housekeeping belongs to lair
and molt. The revision dropped generic ref enumeration and the
delete-then-restore path, and merged on a code-review approval and the
author's instruction, not a fresh verify-gate APPROVED. Its own roar then
preserved one branch held by another session's locked worktree, because
ownership was not established. Ticket 1090 later closed in PR #1408 after the
[remeasurement](../journal/2026/2026-10-14-roar-remeasure-1090.md): against
a same-method October control, median solo Claude Code turns rose from 10
(n=53) to 12.5 (n=14). The earlier 16 → 14 comparison used a mostly
September baseline and does not establish savings.

On 2026-10-12, removing the merged 1085 and 1086 worktrees, git's worktree
guard refused the branch delete until dead-pid locks were unlocked.

## Later exit and temporary-file evidence (2026-10-14)

The [1098 exit-tail revision](../journal/2026/2026-10-14-roar-exit-check-1098.md)
merged as #1409 after rebasing over #1407's retirement of EnterWorktree.
Its roughly three-action exit tail is an estimate, not a measured saving;
post-revision turn savings remain unmeasured in these sources. A local
cross-family reviewer found that ordinary `git worktree remove` deletes
ignored files. The author chose a wording correction and left scanning to
1095. All three round-two external attempts failed; final approval disclosed
DEGRADED coverage.

The [1095 design panel](../journal/2026/2026-10-14-1095-design-panel-pr1399.md)
confirmed that ignored `.tmp/` content is absent from the porcelain WIP check
and can disappear with worktree removal. It also observed pre-WIP `.panel/`
purging. The author selected session-history-assisted candidate reporting and
worktree-owned `.tmp/`, with a disk warning and snapshot exclusion. PR #1399
records the design, not completed implementation; 1095 remains deferred.

## Sources and exceptions

- [Branch-cleanup incidents](../reference_branch_cleanup_incidents.md) — attributed operational note, incidents dated 2026-06-10 and 2026-08-14; its loop description predates the 2026-10-13 rule.
- [Raid 1084/1085/1086](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md) — update-ref measurement; outcome later corrected by the next entry.
- [PR 1374 scope revision and merge](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md)
- [PR 1374 review evidence](../journal/2026/2026-10-13-pr1374-review-evidence/gate-and-author-comments.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
