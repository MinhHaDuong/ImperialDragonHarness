---
name: feedback_measure_whether_a_guard_ever_fired
description: "Before repairing a misfiring guard, check whether its sanctioned path can even trigger it — a guard whose target is only reachable by hand-typing may have guarded nothing for months"
metadata:
  type: feedback
---

`block-pr-merge-in-worktree.sh` exists to stop `gh pr merge` inside a worktree,
its header asserting that git "aborts with `fatal: 'main' is already used by
worktree` in EVERY linked worktree". On 2026-09-08 that premise was contradicted
thirteen times in one night: `skills/merge/erg-pr-merge` calls `gh pr merge` at
four sites and ran from worktrees for PRs 808 through 826 without a single such
failure, and PR 808 was merged by a `gh pr merge` typed by hand from a worktree.

**The structural point is sharper than the count.** The sanctioned merge path is
a *script*, so the PreToolUse hook reads `erg-pr-merge …` and never sees the
string `gh pr merge` at all. The guard's only reachable trigger was a command the
harness tells you not to type. It could not have fired on real work, in either
direction, for as long as it has existed.

**The two questions, in this order, before repairing any guard:**
1. *Can the sanctioned path even trigger it?* If that path is a script or a
   wrapper, a text-matching hook never sees the guarded command, and the guard
   is decorative on the flow that matters.
2. *Has the guarded failure actually occurred recently?* Not "is it plausible" —
   grep the session for the operation succeeding. Thirteen successes is a
   refutation; zero observations either way is not a defence.

`rules/workflow.md` already says prefer deleting a misfiring guard to growing
it. What this adds is how to earn that judgement cheaply instead of arguing it.

**Keep the nuance that survives the refutation.** `gh pr merge --merge` is a pure
API call touching no local git; `gh pr merge --delete-branch` does check out and
delete locally and could genuinely fail in a worktree. So the guard was
plausibly right about one flag and over-broad about the command from birth. A
refutation that deletes the true part with the false part is its own defect —
narrow first, delete only what the measurement actually reaches.

**How to apply:** when a guard misfires, do not open with "restore the matcher".
Open with the two questions. Write the measurement into the ticket so the next
reader inherits evidence rather than a repair plan resting on an unexamined
premise.

Related: [[feedback_harness_cooldown_stop_second_order_tooling]],
[[feedback_editing_a_ticket_body_is_not_appending]].
