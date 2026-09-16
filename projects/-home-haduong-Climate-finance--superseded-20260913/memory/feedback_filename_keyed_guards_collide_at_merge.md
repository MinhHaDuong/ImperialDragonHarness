---
name: feedback_filename_keyed_guards_collide_at_merge
description: "Retiring a generated artifact breaks guards on main that key on its filename; they fire only when the branches meet, so budget a post-merge round"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-27T19:15:12.651Z
---

Deleting a generated artifact is never a local change. Guards and allowlists on
other branches key on the **filename**, and none of them fires until the
branches meet — a green suite on the deleting branch proves nothing.

Retiring `codebook.md` (ticket 0354, 2026-07-27) left stale references in six
places. Three were guards that had landed on main while the branch was open:

- `tests/test_markdown_table_shape.py` pinned it twice — as the sentinel
  Makefile discovery must find (`CANONICAL`), and as the one *shipped* file
  carrying a real escaped pipe;
- `config/unrendered-artifacts.txt` listed it as a deliberately-unrendered
  table (its earned-entry guard fired correctly — that guard is well built);
- Makefile / .gitignore / build script wiring.

Each surfaced as a separate red `make lint` in a separate merge, across two
merges of main. The other three were prose that nothing checks at all
(→ [[feedback_deposit_prose_is_unguarded]]).

**How to apply:** before deleting a generated artifact, `git grep` its basename
across `origin/main`, not just the working branch — including `tests/`,
`config/*.txt`, and `.gitignore` — and expect a second round after each merge
of main. When a repointing is needed, prefer a sentinel that is git-tracked,
built without Phase-1 data, and still exercises the mechanism the guard exists
for; state in the docstring when the replacement is genuinely weaker rather
than letting the rename imply equivalent coverage.

**Why:** the class is invisible to per-PR review by construction — the two
halves live on different branches. Only the merge exercises it, so the merge is
where the budget belongs.
