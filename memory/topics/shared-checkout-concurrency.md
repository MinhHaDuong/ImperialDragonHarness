# Concurrent sessions on one checkout

Scope: episodes of 2026-10-02 to 2026-10-06 in which two or more sessions,
or a session and its subagent, acted on the same primary checkout of this
repository or on the same live user files. Each fact is dated and sourced
below; the applicable rules are `rules/git.md` (branch discipline, no stash,
anchoring git after a fork) and `rules/workflow.md` (Delegation), which this
topic does not restate or extend.

## Supported observations

Unpushable local `main` as a carrier. Direct pushes to `main` are declined by
the repository ruleset (recorded 2026-10-02 in four entries). Commits parked
on local `main` were therefore swept up by whichever session delivered next:
PR #1145 double-carried four commits SHA-identical to open PR #1143's branch,
caught only by the `cross-pr-ticket-collision` check, and was rebuilt from
`origin/main` with the session's own commits. Raid annotations parked on
local `main` landed through another session's wrap PR (#1139) under that
session's attribution; one rebase resolved PR #1138 because both copies
carried the same text. In the 0853/0937/0979/1014 raid one annotation patch
existed as three distinct commits by merge time, resolved by ordered merges,
an auto-dropping rebase and one manual three-file conflict resolution.

The shared annotation base (ticket 1016, option 1). On 2026-10-03 four
wave-1 branches forked from one annotation commit; the per-wave integration
review found zero ticket-file conflicts across all six PR pairs, against the
three divergent copies of 2026-10-02. One wave is one positive case, not a
measured rate.

Other shared-checkout events. `git add tickets/` in the shared checkout swept
a parallel session's untracked ticket into a commit, caught by
`git show --stat` and repaired before push (2026-10-03). A reviewer subagent
briefed "read-only; do not edit, commit, or push" switched branches in the
shared primary checkout and left it on `main`; the parent noticed only through
an unplanned re-read, and no damage followed (2026-10-04, PR #1183). A PR was
merged by a parallel session while its gaze round was still open; the gaze's
ESCALATE fix went through a gated follow-up PR (#1166) rather than reopening
the merged one (2026-10-03).

Live user files. A tournament session's `idh install` from a pre-merge
checkout merged harness hooks back into the live `~/.claude/settings.json`
three minutes after ticket 0887's activation removed them, a double-fire state
detected by PR #1211's review panel; during reproduction a review seat that
did not override `HOME` clobbered the same live file and restored it
sha-verified (2026-10-05). On 2026-10-06 a Vibe tournament session in the
primary checkout acted on review remarks meant for another session; because
`~/.claude/CLAUDE.md` is a symlink to `AGENTS.md`, its uncommitted `AGENTS.md`
edit reached running sessions, one of which corrected its open PR #1223
against the new text. No work was lost; the split of the two sessions' work
went to the author.

## Exceptions and contrasts

The read-only reviewer episode is not a counter-example to the Delegation
rule's wording: the brief forbade edit, commit and push, and the branch switch
was none of these. Whether briefs should name branch switching is a rule
question this memory does not settle. The 1015 entry's suggestion (commit
phase annotations on a short-lived branch or in the wave's wrap PR) is the
author of that entry's proposal; ticket 1016 is the decision record.

## Hypotheses, not facts

That the shared primary checkout is the common factor in these episodes is
a connection between episodes, not an established cause: several also
involve a direct-push refusal, a symlinked instruction file, or a missing
`HOME` override.

## Sources

- [Local main double-carried PR #1143's commits](../journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md)
- [Raid 1015 annotation collision](../journal/2026/2026-10-02-raid-1015-annotation-collision.md)
- [Raid 0853/0937/0979/1014 under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md)
- [Raid 1008, direct push declined](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md)
- [WAVE_BASE first live run](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md)
- [0938 raid, swept untracked ticket](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Reviewer switched the primary checkout's branch](../journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md)
- [0887 live reinstall regression](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md)
- [Two sessions, one set of routing remarks](../journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
