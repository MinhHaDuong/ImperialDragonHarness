---
name: feedback_rebase_can_overwrite_a_sibling_fix
description: "A clean, no-conflict rebase-onto can silently reintroduce stale content into a shared file that main independently fixed elsewhere — diff the full file against the target after rebasing, not just the region the recovery work touched."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c6fa2f07-2da2-48c6-801a-93ba027cd163
  modified: 2026-09-03T15:48:40.822Z
---

Recovered an interrupted Codex session's branch (ticket 0029) and rebased its
commits onto current `main` via `git rebase --onto origin/main <old-base>`.
The rebase reported clean, no conflicts — but one of the replayed commits
touched `bench/fixtures/README.md`, a file `main` had *also* independently
fixed since the branch's base (a HAL sha256 un-pin, commit `e4848b8`). The
replayed commit silently carried the branch's own older, stale version of
that paragraph and its per-record table forward, overwriting main's fix.
A first "repair" pass caught only the prose paragraph (because that's what
the failing test's regex checked) and missed the per-row table showing four
records as hash-pinned when the live `recipe.json` had them null. `/gaze`
review caught the rest by hand-diffing the whole file against `origin/main`.

**Why:** a rebase's "clean, no conflicts" signal means the *patches* applied
without textual collision — it says nothing about whether a replayed patch's
content is now stale relative to independent fixes the target branch made to
the same region. Git has no way to know two edits to the same paragraph were
trying to fix the same underlying fact.

**How to apply:** after rebasing a recovered/stranded branch onto a moved
target, `git diff <target> HEAD -- <file>` on every file the replayed
commits touch, not just the files the recovery's own tests fail on. Where a
test exists that's *supposed* to catch this class (a tally/cross-check
test), verify its actual coverage — a test that regex-matches one paragraph
does not exercise a table in the same file. See [[feedback_verify_the_load_bearing_claim]].
