# Bibliography merge (runbook)

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for the parent skill (this runbook sits under `skills/<parent>/runbooks/`, so anchor on the parent's `SKILL.md`, not on this file). This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

The work is the script `$IDH_ROOT/scripts/bib-merge.py`; this runbook holds its constraints. Merge the ```bibtex fence from a `related-work-note`'s Bibliography
section into a local `refs.bib`. Dedupe against existing entries,
flag conflicts, append new ones, report everything.

## Constraints (non-obvious)

- **Append-only.** The script appends entries; never rewrites or
  reorders existing entries. If refs.bib doesn't exist, script
  aborts with exit 1 — that's a project-setup decision.
- **Never mutate existing entries.** If the note has a field the
  existing entry lacks, report it as a suggestion. Don't write it.
- **Check DOI globally, then author+year.** A normalized DOI match is
  SKIPPED regardless of author or date differences, including within the new
  batch. Otherwise group by first author and `year` (or the year of BibLaTeX
  `date` when `year` is absent). Within that group, differing DOIs denote
  different works; if either DOI is absent, use title similarity (Jaccard ≥ 0.8).
  Rename only conflicting keys; preserve all existing entries and keys.
- **Report suffix-bumps.** Every renamed key must be reported so
  the author can update `\cite{}` calls.
- **Note file is read-only.** Never modify it.
- **`--dry-run`** runs the full logic, prefixes report with
  `DRY-RUN:`, does not write.
- **Local .bib is staging.** Zotero is the system of record from source
  intake. Merge a citation view of already-intaken sources, reusing their
  Zotero identities; this script does not import sources or attach PDFs.

Deduplication does not check work identity against external metadata, relevance
to the manuscript, or support for a cited claim. Complete those checks from
the source and record their evidence separately; an HTTP accessibility PASS
from `validate-refs.py` does not certify them.

## Input

1. Note file path (required) — must have `## Bibliography` with a
   ```bibtex fence. The script auto-extracts the fence.
2. refs.bib path (optional) — default `report/refs.bib` if it exists.
3. `--dry-run` flag (optional).

## Steps

**Step 1 — resolve refs.bib path (if not provided)**

If the user did not provide a refs.bib path, check whether
`report/refs.bib` exists in the current project. If it does, use it.
If neither exists, abort with: `ERROR: no refs.bib found`.

**Step 2 — run the deduplication script (one Bash call)**

```
uv run --script "$IDH_ROOT/scripts/bib-merge.py" <note-file> <refs.bib> [--dry-run]
```

The helper declares its runtime dependencies in PEP 723 metadata. `uv run
--script` resolves them independently of the current paper repository and its
Python environment; no harness virtualenv activation is needed. Directly
executing the helper path uses the same uv entry point through its shebang.

The script:
- Extracts the ```bibtex fence from the note file automatically
- Parses all entries from the fences and refs.bib using the existing
  `bibtexparser` dependency, including inline entries, BibLaTeX `date` and
  macros. Unread plausible entries or undefined macros abort with exit 3
  before any append. A conservative entry-opening count can flag ambiguous
  `@type{` text inside fields/comments; inspect it before retrying.
- Serializes incoming entries only (expanding macros); existing bytes stay intact
- Deduplicates (global DOI; author+year/date and title fallback)
- Appends non-duplicate entries to refs.bib (unless --dry-run)
- Prints a report to stdout

**Step 3 — relay the report**

Print the script's stdout verbatim as the skill output.

## Report format (from script)

```
bib-merge: {note-file} → {refs.bib}
  added:    N
  skipped:  K  (duplicates)
  renamed:  R  (key collisions)
  errors:   E  (malformed entries)
[ADDED] @key
[SKIPPED] @key  (duplicate of @existingkey)
[RENAMED->newkey] @oldkey
```
