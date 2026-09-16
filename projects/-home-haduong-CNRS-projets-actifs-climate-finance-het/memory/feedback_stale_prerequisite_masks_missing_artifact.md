---
name: feedback_stale_prerequisite_masks_missing_artifact
description: "A Make rule whose prerequisite list drifted is not just mis-documented — it exits 0 while producing wrong output, and hides that a required artifact does not exist"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0f40bf6-0077-4e13-a087-1fb24d90b8fb
  modified: 2026-07-27T18:59:25.582Z
---

A per-document prerequisite list that has drifted from what the document
actually uses reads like a documentation problem. It is a correctness problem,
and the failure is silent.

Concrete (ticket 0359, 2026-07-27). `deliverables/multilayer/multilayer.mk`
declared `multilayer-detection.pdf: … $(MULTILAYER_INCLUDES) …` and named no
figure. `MULTILAYER_INCLUDES` listed six top-level includes the paper had
stopped composing — but those files still *existed*, so Make was satisfied.
Result: `make multilayer-detection` **exits 0 and renders a PDF with five
broken image references**, because the five figures it embeds were prerequisites
of nothing. They had never been built at all, which nobody had noticed in
however long. Wiring the real figure list in converts the silent wrong output
into a hard stop — and the hard stop is what exposed the missing artifacts
(ticket 0385).

**Why it hides:** a stale list fails *open*. Make checks the prerequisites you
named, not the ones the document needs, so drift removes checks rather than
adding failures. A green test suite cannot see it either — tests exercise
Python, not the build graph. Three render rules in this repo named no figure at
all and every gate passed.

**How to apply:**

- Treat a prerequisite list as *executable claim*, not documentation. Verify it
  against the source it claims to describe — for Quarto, the transitive
  `{{< include >}}` closure plus embedded image paths.
- Check **both** directions. A surplus entry makes the PDF rebuild on a file the
  document dropped; a missing entry makes it *not* rebuild when a live input
  changes. They fail differently and both matter.
- When a newly-wired prerequisite makes a previously "working" target fail, do
  not treat that as a regression to soften. It is the first honest result that
  target has produced — go find out why the artifact is missing.
- Guard mechanically: `tests/test_deliverable_artifacts.py` diffs every
  `*_INCLUDES` / `*_FIGS` list in `paths.mk` against the real closure, both ways,
  with a redundancy-checked allowlist for deliberate exceptions.

Related: [[feedback_assert_on_written_artifact]] (test the artifact, not the
in-memory record), [[feedback_no_ci_local_merge_gate]],
[[feedback_autodiscovery_class_guard]].
