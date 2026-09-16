---
name: feedback_red_test_the_guard_you_wrote
description: A new guard must be run against the exact defect it was written for; two of three drafts passed the original bug
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 200160eb-e79d-43d2-a7ca-942b18108b18
  modified: 2026-07-28T08:39:08.941Z
---

Before claiming a guard works, reintroduce the specific defect it exists for and
watch it fail. Passing on a renamed-file mutation proves nothing about the bug
you actually set out to catch.

**Why:** On ticket 0292 (2026-07-27) the archive path guard was written to catch
`build_manuscript_archive.sh` copying a root `_quarto.yml` retired by the 0226
reorg. Two successive drafts caught a renamed figure but stayed **green** when
that exact `cp` was pasted back:

1. The path regex was anchored on a leading directory (`deliverables|scripts|…`),
   so a bare repo-root filename never matched. Fixed by tokenising the `cp`
   arguments instead of pattern-matching paths.
2. The "is it a Make target?" fallback used a substring test, and `_quarto.yml`
   occurs inside `deliverables/manuscript/_quarto.yml`. Fixed with a
   token-bounded regex (`(?<![\w./-])…(?![\w./-])`).

Both holes were invisible to the happy-path test and to a rename mutation. Only
replaying the original defect exposed them.

**How to apply:** For each guard, keep a mutation list that includes the
originating defect verbatim, not just a generic rename. Run all of them, expect
red, then restore. If the originating defect cannot be replayed mechanically,
that is itself the finding — the guard is aimed at something other than the bug.
Related: [[feedback_check_the_detector_first]],
[[feedback_assert_on_written_artifact]] (assert on what the tool actually
produced, not on the record you believe it built).

Corollary from the same ticket: a *path* guard cannot catch a layout that
assembles but does not render. The archive that broke had every path resolving
in the repo and none resolving once flattened. Pair a static guard with one
clean-room run of the real artifact.

Second instance, ticket 0360 (2026-07-27), where the broken part was the
**fixture** rather than the assertion. A test for "the post-checkout hook must
never clobber a real `.dvc/cache` directory" built a real cache dir with a
sentinel file, ran the hook, and asserted `is_symlink()` was false and the
sentinel survived. It passed with the guard deleted: `ln -sfn` does not replace
an existing *directory*, it creates the link **inside** it (`.dvc/cache/cache`),
so both assertions hold while the hook misbehaves. Asserting the directory's
full contents (`sorted(p.name for p in d.iterdir()) == [...]`) is what bites.

A second fixture bug in the same test was worse: it created the worktree with a
plain `git worktree add`, and where `core.hooksPath` is configured git fires
post-checkout itself, so the link already existed, `mkdir(exist_ok=True)`
no-oped through it and the sentinel write landed in the real 19 GB shared cache.
Both were found only by deleting the guard and re-running. Generalise: when a
test builds a fixture with a shell primitive, verify the primitive does what you
assume on the *type* of path present (file vs directory vs symlink), and pin any
ambient config the fixture depends on (`-c core.hooksPath=/dev/null`) rather
than inheriting the machine's.

Third instance, ticket 0357 (2026-07-28), and the cheapest kind to avoid.
A guard was written so the README could not keep describing a defect after it
was fixed: for each registered document, fail if the prose says it is "absent
from" the registry. Written, run, green, and **blind**. Replaying the actual
README paragraph passed it. The regex was
`rf"{doc}\b[^.\n]{{0,80}}absent from"` — a proximity window — and in the real
text the document name and the phrase sat on *different lines* with a sentence
boundary between them, both of which the character class excluded. Rewritten to
split on blank lines and ask "does any paragraph containing 'absent from' also
name a registered document?", it fires.

Generalise beyond this repo: **a proximity regex is the wrong shape for a prose
guard.** Prose wraps where the editor's margin falls and breaks sentences where
the argument does, so the distance between two related words is not a property
of the text — it is an accident of formatting that changes on the next reflow.
Scope prose checks to a structural unit the author controls (paragraph,
section, list item), never to a character or line window. The tell that this
mistake is live: your test data is a single synthetic line and the real target
is a wrapped paragraph.
