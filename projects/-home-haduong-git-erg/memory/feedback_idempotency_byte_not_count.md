---
name: feedback_idempotency_byte_not_count
description: "Test idempotent file-writers by byte-comparing reruns, not by counting markers — count tests miss whitespace growth"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 211826a9-1beb-4f8d-9a7a-952c56d075ef
---

When a command edits a file in place and claims idempotency (managed-block
upsert, install --hooks, inject-agents), a `grep -c marker` test that only
counts occurrences PASSES while the file silently grows a blank line on
every rerun (separator inserted by both the strip and the re-insert step).
PR #243's marker-count idempotency test passed; a byte-compare caught 3
extra blank lines over 3 runs.

**Why:** marker count is invariant under separator accumulation; only the
byte content reveals the drift, and accumulation is a real bug (the file
is never byte-stable, breaking any "file unchanged" downstream check).

**How to apply:** for any in-place editor, add a test that runs the
command twice and asserts `after1 = after2` byte-for-byte (capture with
`$(cat file)` and string-compare, or cmp). Make the upsert reach a fixed
point on the first application: guard separator insertion against an
already-blank boundary. Pairs with [[feedback_verify_pushes_fixes]].

**Corollary — a PREPENDED managed hook block must NEVER end in `exit 0`**
(any hook: pre-commit, pre-push). It is inserted before pre-existing
third-party content, so a trailing `exit 0` silently disables everything
below it. The block's natural fall-through (a closing `fi`, or an `if`
with a false condition and no else) already exits 0, so it composes with
third-party content instead of shadowing it. Test it: pre-place
third-party content, install, assert the third-party part still runs.
(Bit twice: 0208 pre-commit caught by council; 0209 pre-push exit 0
reintroduced and caught by /verify.) And the recipe a warn-hook prints
must itself be correct: `erg archive` renames files, so the advice must be
`git add tickets/ && git commit` (NOT `git commit -am`, which stages only
the deletion and orphans the moved file).
