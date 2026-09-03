---
name: feedback_merge_is_one_command
description: "merge" means run the merge; do not stack a CI probe, a merge-config read and a full make check in front of it
metadata:
  type: feedback
---

When the author says "merge", merge. On PR #206 (a docs-only note closing no
ticket) I first queried `statusCheckRollup`, then read the repo's
squash/merge/rebase config, then ran the full `make check` — and only then
merged. His verdict: "That's too much ceremony for merge."

**Why:** the gates are for changes that can break something. A markdown note
under `verification/` that adds no ticket and no figure cannot fail `erg check`,
the figures guard, or pytest, and re-proving that in front of him spends his
attention to buy nothing. Verification is owed where a claim is load-bearing,
not as a ritual before every button press. It is the same over-application the
harness warns about with ticket ID renumbering: the right move at creation time
is not the right move everywhere.

**How to apply:** for a docs-only or otherwise inert PR, `gh pr merge <N> --merge`
and confirm it landed. That is the whole procedure.

Keep the gate where it earns its place: a PR touching `bench/` drivers, figures
quoted in prose, tickets, or fork TypeScript. There, run the suite before
merging — see [[feedback_rerun_gate_after_own_fix]] and
[[feedback_green_prs_red_union]].

Read the merge method only when a merge actually bounces; this repo allows all
three and its history uses merge commits, with `delete_branch_on_merge` true so
the branch cleans itself up.
