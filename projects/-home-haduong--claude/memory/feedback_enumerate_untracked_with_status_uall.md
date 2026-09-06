---
name: feedback_enumerate_untracked_with_status_uall
description: "git clean -n prefixes 'Would remove ' and lists whole directories, not their files; enumerate untracked paths with status --porcelain -uall before deciding anything is safe to delete"
metadata:
  node_type: memory
  type: feedback
---

Two verification scripts in one session, both wrong, both about the same
command. `git clean -nd projects/ tickets/` is the wrong instrument for
answering "which untracked files would I lose?", in two independent ways:

- **Its output is prose, not paths.** Each line reads `Would remove <path>`.
  A `while read -r _ f` drops only the first word, so `f` becomes
  `remove <path>` and every lookup against it fails. The failure branch then
  prints for all 29 paths, which reads as a catastrophic finding and is
  really an empty measurement.
- **It collapses a wholly-untracked directory into one entry**, so the files
  inside are never enumerated. Filtering those trailing-slash lines out (to
  handle them "separately") silently drops seven real files, which then
  aborted the fast-forward they were supposed to have cleared.

Use `git status --porcelain --untracked-files=all | grep '^??' | cut -c4-`.
It emits one bare path per file, descends into untracked directories, and
needs no parsing.

**Why:** both defects share a shape the harness already names for checks that
return nothing. This is its mirror: a check that returns *everything*. An
all-positive result feels like alarming evidence, so it escapes the scepticism
a null result would attract, and it is just as compatible with "the probe
never looked". The first version reported 29 files at risk when the true
answer was one; the second reported clean when seven files still stood.

**How to apply:** before acting on a list that a script derived from a
porcelain-free git command, spot-check one entry by hand. Here, a single
`git cat-file -e origin/main:<the first path>` typed manually would have
exposed both bugs in seconds. And when the decision is a deletion, verify
each file byte-for-byte against the ref immediately before removing it, in
the same loop, so a file written between check and delete is skipped rather
than lost. See [[feedback_verify_each_before_batch_action]] and
[[reference_git_under_rtk_and_the_worktree_guard]].
