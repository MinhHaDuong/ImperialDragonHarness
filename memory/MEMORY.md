# Project memory

v8 repository memory, rebuilt by department at each smelt (prompt
[SMELT.md](SMELT.md)). Provenance: [inventory](../conception/memory-v8/source-inventory.md),
[revisions](../conception/memory-v8/source-revisions.tsv).

## Departments

- [Commission](topics/commission.md) — the author's pinned rulings; a ruling
  waits there until the author promotes it.
- [Site practice: git, worktrees, sessions](topics/git-worktree-session-guards.md)
  — the primary checkout is the author's workspace; agents on branches; push
  by commit id so the exit code answers.
- [Site practice: raids, review, merging](topics/raid-review-and-merge.md) —
  gate records bind base and head: a moved main stales them; record, retry once.
- [Site practice: CI, tests, doctors](topics/ci-and-test-suite.md) — `make check`
  workers clamp to 2..24; field median about 75 s on a shared padme.
- [Environment: hosts and services](topics/host-environment.md) — padme 32 cores
  / 64 threads; one data store under `DATASETS_DIR/ours`; Zotero is local-only.
- [Environment: runtimes and models](topics/runtime-observations.md) — pin `model`
  on every launch; resident rules reach Codex and Pi via generated AGENTS.md.
- [Architecture: the memory system](topics/memory-v8-governance.md) — journal is
  the append-only source; 1349 closed, rebuilds count from the accepted fifth smelt.
- [Architecture: skills, docs, hooks](topics/skills-docs-and-hooks.md) — the
  catalog is generated: `make skills-catalog` after frontmatter changes.

## Smelts

- [Sixth smelt](smelts/2026-11-01-sixth-smelt.md) — this run; submitted, not yet
  accepted.
- [Fifth smelt](smelts/2026-10-30-fifth-smelt.md) — first rebuild (1349);
  accepted by the author 2026-10-31 (PR #2049, merged 52f63b18), ticket closed.
- [Fourth smelt](smelts/2026-10-15-fourth-hoard.md) — accepted.

History is the journal (`journal/YYYY/`), the smelt reports and git; it has no
page. Attribution records: `evidence/attribution/`.
Search the journal for older or unprocessed experiences.
