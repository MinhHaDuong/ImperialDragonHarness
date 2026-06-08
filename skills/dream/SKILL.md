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

If `--dry-run`: **skip write/commit steps (5, 6, 7, 8, 11, 12) but still run the read-only promotion pass (9–10) and decay pass (13) and print their reports.** Then stop.

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

**7. Record provenance.**

For each surviving entry (NOOP, ADD, UPDATE), record its presence in this project's consolidation:

```bash
python3 ~/.claude/skills/dream/provenance.py record <entry_slug> <project>
```

`<entry_slug>` is the entry's filename without extension (e.g. `feedback_vim`). This tracks which projects have seen each entry, enabling the promotion pass.

**Slug identity (v2 simplification)**: entries are keyed by filename. If the same lesson appears under different filenames in different projects, Claude should assign the same slug during consolidation to enable cross-project frequency counting. A semantic slug-matching system is deferred to v3.

**7b. Confirm still-relevant promoted entries.**

A promoted entry's project-level copy is a tombstone, so step 7's `record` never
fires for it again and its `last_confirmed` would freeze — decay-flagging it at
90 days no matter how relevant it remains (ticket 0224). For each harness-level
entry (in `~/.claude/memory/`) that this project's surviving content still
supports — i.e. the consolidation would have classified its lesson NOOP or
UPDATE were it still project-local — refresh its confirmation:

```bash
python3 ~/.claude/skills/dream/provenance.py confirm <slug>
```

This resets only the decay clock; it does not re-add the project to the entry's
origin list. Skip entries the project's content no longer supports — letting
those decay-flag is the intended signal for human review.

**8. Commit.**

`commit.py` commits into `~/.claude` directly. The `~/.claude` pre-commit hook
**refuses a commit on `main` in the primary checkout** (everything lands via
branch + PR). Before committing, ensure `~/.claude` is on a branch, not main:

```bash
git -C ~/.claude rev-parse --abbrev-ref HEAD   # must NOT print "main"
# if it does: git -C ~/.claude switch -c dream-consolidate-$(date +%F)
python3 ~/.claude/skills/dream/commit.py commit <project> <n_before> <n_after>
```

Then push the branch and open a PR for the consolidation (do not merge to main
directly). The override `ALLOW_MAIN_COMMIT=1` exists for deliberate cases only —
do not use it to bypass the branch-and-PR flow during a routine dream.

### Promotion pass

Runs after consolidation. Evaluates whether any project-level entries have earned harness-level status.

**9. List promotion candidates.**

```bash
python3 ~/.claude/skills/dream/provenance.py candidates
```

Output is JSON: entries seen in >=2 distinct projects that are not yet promoted. If empty, skip to step 13.

**10. Evaluate each candidate against three gates (all required).**

For each candidate, Claude evaluates inline:

- **Frequency gate** (mechanical, already passed): entry appears in >=2 distinct project consolidations.
- **Cost gate** (Claude judgment): would missing this entry cost >500 tokens to re-derive per session, OR does missing it risk correctness/security failures? If neither, the entry fails.
- **Context-independence gate** (Claude judgment): apply the three-part test from the research note:
  1. Entity stripping: remove project-specific entities. Does the lesson retain meaning?
  2. Reformulation: rewrite in domain-neutral terms. Is it still actionable?
  3. Counterfactual transfer: would this have prevented a known failure in a different project?

Log each gate evaluation with one line of reasoning per candidate.

**11. Apply approved promotions.**

For each candidate that passes all three gates:

a. Write the context-independent reformulation to `~/.claude/memory/<slug>.md`.
b. Mark promoted in provenance:
```bash
python3 ~/.claude/skills/dream/provenance.py promote <slug>
```
c. Overwrite the project-level entry with a tombstone:
```
# PROMOTED <ISO timestamp>: <title>
# Now at: ~/.claude/memory/<slug>.md
# Original content preserved in git history.
```

If `--dry-run`: print candidates, gate evaluations, and proposed promotions without writing anything.

**12. Commit promotions.**

As in step 8, ensure `~/.claude` is on a branch (not main) before committing —
the primary-checkout pre-commit hook refuses main commits.

```bash
python3 ~/.claude/skills/dream/commit.py commit <project> <n_before> <n_after>
```

### Decay pass

Runs after the promotion pass. Flags stale harness-level entries for review.

**13. Check for stale harness entries.**

```bash
python3 ~/.claude/skills/dream/provenance.py decay
```

Output is JSON: promoted entries whose `last_confirmed` date is >90 days ago. For each flagged entry, print:

- Entry slug and title
- Last confirmed date and age in days
- Originating projects

These entries need human review: confirm (update `last_confirmed`), demote back to project level, or delete.

If `--dry-run`: print the decay report without taking any action.

## Schedule recipe

One entry per project:

```
0 2 * * * /dream <project>
```

To inspect consolidation history:
```bash
git log --grep='^dream: consolidate' --oneline
```

## v2 features (ticket 0165)

- Harness-level memory tier (`~/.claude/memory/`) + earned promotion (three-gate: frequency, cost, context-independence)
- Provenance tracking (`.provenance.json`) — cross-project entry history
- Harness decay (90-day unconfirmed entries flagged for review)
- Dry-run mode covers promotion candidates and decay flags

## v3 roadmap

- Importance-weighted trigger (SCM pattern)
- Temporal-hierarchical reflection (TiMem) for multi-session horizons
- Link updates after UPDATE/DELETE passes (A-MEM)
- Bi-temporal metadata (Graphiti pattern) for richer decay
