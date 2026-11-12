# Project memory

v8 repository memory, rebuilt by department at each smelt; instructions live
in the Smelt skill. Provenance: [inventory](../design/memory-v8/source-inventory.md),
[revisions](../design/memory-v8/source-revisions.tsv).

## Departments

- [User rulings](topics/user-rulings.md) — contextual decisions and author edits persist;
  Brood integrates and retires integrated rulings.
- [Git, worktrees, sessions](topics/git-worktree-session-guards.md) — primary
  is the author's workspace; clean up your own tree; force-push alone in its call.
- [Raids, review, merging](topics/raid-review-and-merge.md) — records bind
  base/head; a refused gated landing waits for the author's "Land <PR>".
- [CI, tests, doctors](topics/ci-and-test-suite.md) — check and check-fast on
  workers; on an after-merge red, read after-merge.log before blaming main.
- [Hosts and services](topics/host-environment.md) — one transcript archive;
  Zotero identity by attachment md5, then identifiers, title last.
- [Runtimes and models](topics/runtime-observations.md) — context ceilings live
  in route's ceilings.json; requested pins are not observed identities.
- [Memory system](topics/memory-v8-governance.md) — blueprint in
  design/memory-v8/README.md; grep memory/ before archiving a ticket.
- [Skills, docs, hooks](topics/skills-docs-and-hooks.md) — generated catalog;
  a contract is cited rather than paraphrased.

## Smelts

- [Eighth](smelts/2026-11-10-eighth-smelt.md) — proposed, awaiting the author.
- [Seventh](smelts/2026-11-08-seventh-smelt.md) — accepted by the author
  2026-11-08; PR #2263.
- [Sixth](smelts/2026-11-01-sixth-smelt.md) — accepted 2026-11-05 (PR #2197).
- [Fifth](smelts/2026-10-30-fifth-smelt.md) — accepted (PR #2049).

History: `journal/YYYY/`, reports and git; attribution: `evidence/attribution/`.
Native store: Claude Code auto-memory keyed by the primary checkout; inventory
with `scripts/smelt_native_notes.py`. Accepted native text is in the reports'
linked annexes; unavailable or uncleared notes stay unknown.
