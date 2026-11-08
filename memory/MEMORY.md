# Project memory

v8 repository memory, rebuilt by department at each smelt; instructions live
in the Smelt skill. Provenance: [inventory](../conception/memory-v8/source-inventory.md),
[revisions](../conception/memory-v8/source-revisions.tsv).

## Departments

- [User rulings](topics/user-rulings.md) — contextual decisions and author edits persist;
  Brood integrates and retires integrated rulings.
- [Git, worktrees, sessions](topics/git-worktree-session-guards.md) — primary
  is the author's workspace; setup links must not point to a tree's sole copy.
- [Raids, review, merging](topics/raid-review-and-merge.md) — records bind
  base/head; filing PRs must not use a Ticket close-claim line.
- [CI, tests, doctors](topics/ci-and-test-suite.md) — workers clamp 2..24;
  new doctor diagnostics run on demand, outside routine gates.
- [Hosts and services](topics/host-environment.md) — one transcript archive;
  Zotero exact identity remains distinct from filename candidates.
- [Runtimes and models](topics/runtime-observations.md) — launch pins do not
  establish a masked served identity; runtime observations are dated.
- [Memory system](topics/memory-v8-governance.md) — append-only journal;
  Smelt nominates, separately authorized Brood discusses promotion.
- [Skills, docs, hooks](topics/skills-docs-and-hooks.md) — generated catalog;
  a contract is cited rather than paraphrased.

## Smelts

- [Seventh](smelts/2026-11-08-seventh-smelt.md) — accepted by the author
  2026-11-08; PR #2263.
- [Sixth](smelts/2026-11-01-sixth-smelt.md) — accepted 2026-11-05 (PR #2197).
- [Fifth](smelts/2026-10-30-fifth-smelt.md) — accepted (PR #2049).
- [Fourth](smelts/2026-10-15-fourth-hoard.md) — accepted.

History: `journal/YYYY/`, reports and git; attribution: `evidence/attribution/`.
Native store: Claude Code auto-memory keyed by the primary checkout; inventory
with `scripts/smelt_native_notes.py`. Accepted native text is in the reports'
linked annexes; unavailable or uncleared notes stay unknown.
