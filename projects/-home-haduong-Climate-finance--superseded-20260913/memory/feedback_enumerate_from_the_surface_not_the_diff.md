---
name: feedback-enumerate-from-the-surface-not-the-diff
description: "Enumerate a defect class from its authoritative discovery surface, and re-run that enumeration at merge — a long-lived PR's exit criterion is checked against main, not against the tree the sweep saw"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c005a06f-79a6-403f-9684-c3dbe29124f2
  modified: 2026-07-27T19:12:15.253Z
---

When a ticket's exit criterion is "no X does Y", enumerate X from the
project's authoritative discovery surface (here `tests/_mk_discovery.generated_markdown_targets()`,
which reads Make rules), never from the diff that surfaced the problem — and
**re-run the enumeration at merge**, not only when the sweep is first written.

**Why:** enumerating from the diff reproduces the diff's scope, not the
problem's. Ticket 0370 (2026-07-27) filed a follow-up naming the two gitignored
tables its diff touched; `git check-ignore` over the discovery list showed
five, i.e. half the guard's surface was blind, not two files at its edge. The
same PR's sweep reported 8 targets and merged against a main that had 10 —
ticket 0327 added `export_corpus_flow.py`, a fresh instance of the very defect
class, while the PR was open. Merging then would have landed a PR whose own
exit criterion was false.

**How to apply:** find the repo's discovery helper before hand-rolling a list.
Put the enumeration in the *verification* step, not just the action step, and
re-run it after every `git merge origin/main` on a PR that has been open across
other merges. If the count moved, the new instances are in scope — a defect
class does not stop accruing members because your branch is open.

Related: [[feedback_autodiscovery_class_guard]], [[feedback_render_oracle_for_generated_markup]],
[[feedback_no_ci_local_merge_gate]].
