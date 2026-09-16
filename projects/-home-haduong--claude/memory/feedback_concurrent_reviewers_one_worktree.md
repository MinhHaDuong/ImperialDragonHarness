---
name: feedback_concurrent_reviewers_one_worktree
description: "Two review agents in one worktree corrupt each other when either mutates files to test them — stale .pyc from one reviewer's injected defect produced phantom failures for the other"
metadata:
  type: feedback
---

Running two review agents concurrently against the **same worktree** is unsafe
whenever either of them writes, and a good reviewer writes: the way to prove a
test actually catches a defect is to re-inject the defect and watch the test
fail.

Observed 2026-09-16 on PR #925. Two Sonnet reviewers were launched in parallel
on one worktree — one resumed (adjudicating its own earlier findings), one
fresh. The resumed reviewer re-injected the original broken literals into two
scripts, ran the tests, confirmed the failures, and restored the files. Correct
method. But Python had meanwhile compiled `.pyc` files from the broken source,
and the fresh reviewer's first `make check` showed **three phantom failures**
from that stale bytecode. It diagnosed the artifact, cleared `__pycache__`, and
re-ran clean — so nothing was lost, by its competence rather than by design.

**Why:** a reviewer's mutation window is invisible to the other reviewer and to
the coordinator. The damage is not the source file, which gets restored, but
everything *derived* from it while it was wrong — bytecode, caches, build
outputs, anything with its own staleness rules. A restored tree can still be
poisoned, and `git status` says clean throughout.

**How to apply:** give each reviewer its own worktree, or run them
sequentially. The same rule already applied to the coordinator — during this PR
a `.erg` fix was deliberately deferred so as not to edit the tree under a
running reviewer — and it was simply not extended to the reviewers themselves.
When it is too late, clear derived artifacts (`find . -name '*.pyc' -delete`)
before believing any test result from the overlap window.

Related: [[feedback_shared_worktree_live_session_contention]],
[[feedback_a_test_green_for_an_accidental_reason]].
