# Project memory

v8 repository memory, rebuilt by department at each smelt (prompt
[SMELT.md](SMELT.md)). Provenance: [inventory](../conception/memory-v8/source-inventory.md),
[revisions](../conception/memory-v8/source-revisions.tsv).

## Departments

- [Commission](topics/commission.md) — the author's pinned rulings; a ruling
  waits there until the author promotes it.
- [Site practice: git, worktrees, sessions](topics/git-worktree-session-guards.md)
  — plain worktrees (add, lock, `cd`); push by commit id so the exit code answers.
- [Site practice: raids, review, merging](topics/raid-review-and-merge.md) —
  gate records bind base and head: a moved main stales them; record, retry once.
- [Site practice: CI, tests, doctors](topics/ci-and-test-suite.md) — `make check`
  workers clamp to 2..24; field median about 75 s on a shared padme.
- [Environment: hosts and services](topics/host-environment.md) — padme 32 cores
  / 64 threads; Zotero is local-only.
- [Environment: runtimes and models](topics/runtime-observations.md) — pin `model`
  on every launch; children inherit the session model.
- [Architecture: the memory system](topics/memory-v8-governance.md) — journal is
  the append-only source; Claude Code rarely reads this store (ticket 1350).
- [Architecture: skills, docs, hooks](topics/skills-docs-and-hooks.md) — the
  catalog is generated: `make skills-catalog` after frontmatter changes.

## Smelts

- [Fifth smelt](smelts/2026-10-30-fifth-smelt.md) — first rebuild (1349);
  submitted, not yet accepted.
- [Fourth smelt](smelts/2026-10-15-fourth-hoard.md) — accepted.

History is the journal (`journal/YYYY/`), the smelt reports and git; it has no
page. Attribution records: `evidence/attribution/`.
Search the journal for older or unprocessed experiences.
