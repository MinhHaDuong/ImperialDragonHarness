---
name: feedback_content_match_recovery_needs_diff_verification
description: "Recovering lost uncommitted content from dangling git blobs by keyword/filename match alone found the wrong blob in a shared, concurrently-edited checkout — verify the candidate's diff size against an independently-measured baseline before trusting it"
metadata:
  node_type: memory
  type: feedback
---

After destroying uncommitted edits to two files (see
[[feedback_blocked_compound_command_skips_every_line]]), I recovered them from
dangling blobs left by an earlier `git add -A`, found via `git fsck
--unreachable` and matched by grepping blob content for the expected filenames
and frontmatter. For two of the recovered files the match was correct. For two
others — both project `MEMORY.md` index files — the grep matched a blob that
was a much larger, unrelated rewrite (a full pass adding descriptions to every
existing entry) instead of the small pending edit that had actually been
sitting in the working tree.

**Why:** keyword matching finds *a* blob containing the expected content, not
*the* blob that was actually on disk at the time of loss — and `~/.claude` is
a checkout multiple concurrent sessions edit directly (confirmed live during
this same incident: `rules/README.md`, `rules/workflow.md` and the harness's
own `MEMORY.md` changed on disk mid-session from other sessions' commits). A
different session's own in-progress, uncommitted edit to the same file can be
swept into the same `git add -A` and left as an equally-matching dangling
blob. The mismatch was invisible until a CI budget guard failed on the
oversized reconstructed file — nothing else would have caught it, since both
versions "look like" legitimate content.

**How to apply:** before trusting a content-matched blob, diff it against the
file's actual HEAD/main baseline and compare the line count to whatever was
independently measured *before* the loss (an earlier `git diff --stat`, if one
was captured). A blob whose diff size doesn't match the original measurement
is not the target content, however plausible its text reads. When no such
independent measurement exists, prefer the smallest/most conservative
reconstruction consistent with what actually needs to change, over the richest
matching blob.

Related: [[feedback_blocked_compound_command_skips_every_line]].
