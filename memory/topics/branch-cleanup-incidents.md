# Branch-cleanup incidents

Scope: the evidence behind the guards in the branch-cleanup loops of
`rules/git.md` (ticket 0242, ratcheted by `tests/test_branch_cleanup_recipes.py`).
An attributed operational note: each incident is dated in the source; assess
against current rules before extending any guard.

## Supported observations

The source note attributes one incident per guard. An unguarded loop deleted
local `main` during a hygiene pass (2026-06-10), recovered by re-tracking
`origin/main`. An unguarded remote sweep hit the bare `origin` symref that
`${ref#origin/}` does not strip, aborted under `set -e` on its first iteration
and left every stale branch in place (2026-08-14). `-d` checks
merged-into-HEAD rather than merged-into-`origin/main`, so it spuriously
refuses merged branches after the ancestry probe has already proven
containment — which is why the loops use `-D` inside that probe and never
outside it. The loops key on exit status rather than parsed output because a
parsed-output pipeline silently no-opped under rtk's output rewriting before
v0.45.0.

## Sources and exceptions

- [Branch-cleanup incidents](../reference_branch_cleanup_incidents.md) — attributed operational note, incidents dated 2026-06-10 and 2026-08-14.
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
