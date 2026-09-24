---
name: feedback_merge_permission_needs_review_and_author_words
description: "In auto mode the permission layer denies a merge with no recorded review, a push to a branch other than the session's own, and an edit that relaxes a ratified rule in the author's name — each clears on the specific evidence, not on persistence"
metadata:
  type: feedback
---

On 2026-09-24 (cloud session, coherence train 0956) three actions were denied,
each for a different reason, and each cleared the same way: by supplying the
thing the denial named.

- A tickets-only PR merged without review; the next merge attempt in the batch
  was denied as "merge without review". Cleared by an independent reviewer's
  verdict posted on every PR page, then the author's "yes" to merge.
- A fix pushed to someone else's PR branch was denied: the session's designated
  branch is the only one it may push. Cleared when the author explicitly
  authorized pushing to that PR.
- Rewriting search-works' ratified merge-authority rule on the author's chat
  ruling ("harness wins") was denied as instruction poisoning: the edit relaxed a
  safety rule and quoted the author. Cleared when the author gave the
  instruction verbatim; the new DECISIONS entry quotes those words.

**Why:** the layer judges the outcome, not the command, and it cannot see chat
approvals that were not stated as instructions for that action.

**How to apply:** do not retry or reword a denied action. Name the missing
evidence to the author — review record, explicit push permission, their own
words for a rule change — get it, record it where the next reader finds it (PR
page, DECISIONS entry), then act once.
