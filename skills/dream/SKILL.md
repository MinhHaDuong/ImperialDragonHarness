---
name: dream
description: Autonomous nightly memory consolidation for one project.
user-invocable: true
---

# Dream — memory consolidation

Consolidates and deduplicates memory for one project using mem0 classifier + Park reflection. Claude does all reasoning inline; scripts handle only file I/O and git.

## Invocation

```
/dream <project> [--dry-run]
/dream <project> --rollback <commit-hash>
```

`<project>` is the directory name under `~/.claude/projects/` (e.g. `-home-haduong--claude`).

## Steps

### Rollback mode

If `--rollback <hash>` is present, run:
```
python3 ~/.claude/skills/dream/commit.py rollback <hash>
```
Then stop.

### Consolidation

**1. Read the memory index.**

```bash
python3 ~/.claude/skills/dream/read-index.py <project>
```

Output is JSON: `{project, memory_dir, entries[]}` where each entry has `filename`, `title`, `desc`, `content`, `path`.

If `entries` is empty, log "No memory entries found" and stop.

**2. Classify each entry.**

For each entry, read its `content` and the content of semantically related entries (look for keyword overlap in titles and descriptions). Then decide:

- **NOOP** — already accurate and not redundant with another entry.
- **ADD** — genuinely new information with no semantic equivalent (rare; most entries were already classified when written).
- **UPDATE** — should be merged into or superseded by another entry.
- **DELETE** — contradicted by a more recent entry, or fully stale.

Rules:
- Preserve entries that document evolution ("use vim" → "use emacs"): keep both unless one is explicitly obsolete.
- Only DELETE if the entry is genuinely misleading or already captured elsewhere.
- Log each decision with one line of reasoning.

**3. Reflect on survivors.**

From entries classified NOOP, ADD, or UPDATE: extract 5 high-level insights that capture patterns, recurring themes, or important lessons. Each insight: 1–2 sentences. These go into the regenerated index as context above the entry list.

**4. Report.**

Print a summary table:
- Each filename → decision + one-line reason
- The 5 extracted insights
- Counts: N entries before → M after

If `--dry-run`: **stop here. Do not write anything.**

**5. Apply deletions.**

For each DELETE entry, overwrite its file with a tombstone:
```
# DELETED <ISO timestamp>: <title>
# Reason: <one-line reason>
# Original content preserved in git history.
```

Use the Edit or Write tool. Never use `rm`.

**6. Rewrite MEMORY.md.**

Write a new `MEMORY.md` at `<memory_dir>/MEMORY.md` with this structure:

```markdown
## Key insights

- <insight 1>
- <insight 2>
...

## Entries

- [<title>](<filename>) — <desc>
...
```

Include only surviving entries (NOOP, ADD, UPDATE). Keep the index under 200 lines.

**7. Commit.**

```bash
python3 ~/.claude/skills/dream/commit.py commit <project> <n_before> <n_after>
```

## Schedule recipe

One entry per project:

```
0 2 * * * /dream <project>
```

To inspect consolidation history:
```bash
git log --grep='^dream: consolidate' --oneline
```

## v2 roadmap

- Harness-level memory tier + earned promotion (ticket 0163)
- Importance-weighted trigger (SCM pattern)
- Temporal-hierarchical reflection (TiMem) for multi-session horizons
- Link updates after UPDATE/DELETE passes (A-MEM)
