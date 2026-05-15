---
name: dream
description: Autonomous nightly memory consolidation across all projects.
disable-model-invocation: false
user-invocable: true
---

# Dream — autonomous nightly memory consolidation

Consolidates and deduplicates memory across all projects (`~/.claude/projects/*/memory/`). Runs nightly as a scheduled agent or manually on demand.

## When to run

- **Scheduled**: nightly (default `0 2 * * *`, 2 AM UTC). Configure via `/schedule 0 2 * * * /dream`.
- **Manual**: user invokes `/dream` after work sessions (especially when memory churn is high) or `/dream <project>` to consolidate a single project.

## Design (research validated 2026-05-13)

Uses three techniques from published literature:

1. **mem0 classifier (ADD/UPDATE/DELETE/NOOP)**: For each memory entry, retrieve semantic neighbors and prompt LLM to classify. Prevents silent dedup drift.
2. **Park 2023 reflection**: After dedup, extract N=5 high-level insights from survivors and regenerate `MEMORY.md` index.
3. **Bi-temporal invalidation**: Never delete files; apply edits in place. Git audit log provides recovery.

All patterns are production-ready as of 2026-05-13 (see `docs/dream-research.md` for full reconciliation with current state-of-art).

## Procedure

1. **Dry-run check** — if `--dry-run` flag, propose edits and exit without writing.
2. **Per-project iteration**:
   a. Read `MEMORY.md` index + all `.md` memory files.
   b. For each entry: retrieve top-5 neighbors by keyword-overlap (Counter frequency heuristic; v2 will use vector embeddings).
   c. Prompt LLM: given candidate X and neighbors, decide ADD (new) / UPDATE (augment) / DELETE (contradicts) / NOOP (present).
   d. Apply edits in place (tombstone comments for deleted entries; never `rm`).
   e. Extract N=5 insights via reflection prompt.
   f. Regenerate `MEMORY.md` from insights + survivors (keep index < 200 lines).
   g. Commit with message: `dream: consolidate <project> memory (<n>→<m>)`.
3. **Post-consolidation**: git operations confined to IDH; no writes to project repos.

## Flags

- `--dry-run`: Propose edits, print diffs, exit without writing.
- `--rollback <commit-hash>`: Revert last consolidation commit.
- `--project <name>`: Consolidate single project (default: all projects).
- `--model <model-id>`: Override default model (default: haiku-4-5-20251001). Use for testing or cost control.

## Schedule recipe

Add to `/schedule` (or cron):

```
0 2 * * * /dream
```

Runs nightly at 2 AM UTC. To inspect consolidation results:

```
git log --grep='^dream:' --oneline
```

## v2 roadmap (post-MVP, Q3+ 2026)

- Importance-weighted trigger (SCM pattern, April 2026)
- Temporal-hierarchical reflection (TiMem, January 2026) if projects track session boundaries
- Zettelkasten link updates (A-MEM, February 2025) after UPDATE/DELETE passes
- Explicit `t_valid`/`t_invalid` metadata in memory entries (complement git audit log)
- Consolidation benchmarking (LoCoMo / LongMemEval-S metrics)
