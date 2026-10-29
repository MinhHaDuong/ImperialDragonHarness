---
metadata:
  category: memory
  order: 1
name: smelt
description: "Consolidate one project's repository memory, pruning stale or contradicted claims, without proposing rules. Use to tidy accumulated memory; not for new facts (/roar)."
user-invocable: true
---

# Smelt — project memory consolidation

Use `/smelt <project-repository> [--dry-run]`. The explicitly selected project
repository is the destination; the installed skill directory is never a
destination. Read its AGENTS.md and inspect its memory convention. Missing
paths or permissions are visible failures; do not create a replacement store
in the harness or use retired shared/native-store helpers.

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"`
in the same shell call. Substitute the absolute SKILL.md path or skill directory supplied by the
runtime (a pre-set `IDH_ROOT` wins); this physically resolves the installed projection to its canonical
checkout. Never derive the helper root from the selected project's cwd.

## Migration preflight

Run sequentially: preflight, isolate, migrate, then consolidate. Migration must
finish successfully before the new-format prompt or reports are used.

Set `PROJECT` to the selected repository's absolute path. Inventory additional
active reference files explicitly as project-relative paths; start with
`REFERENCES=(--reference AGENTS.md)` and add only inspected active references.
The helper already includes the prompt, index and Markdown topics. Do not
inventory journal entries, accepted reports, historical ledgers or ciphertext;
never sweep other projects or the installed harness.

Preflight reads inputs and describes the one-way migration:

```bash
python3 "$IDH_ROOT/scripts/smelt_migrate.py" "$PROJECT" "${REFERENCES[@]}" --dry-run
```

Stop visibly on a conflict, unreadable input, filesystem indirection or helper
failure; preserve both conflicting paths. If invoked with `--dry-run`, report
this plan and stop here without writes, branches or commits. Old names are
recognized only by this migration preflight, never as consolidation inputs.

For a writing run, enter an isolated checkout and dedicated branch of the
selected project, leaving its primary checkout and unrelated changes alone.
Set `PROJECT` to that isolated checkout; retain the inspected relative
`REFERENCES` inventory. Apply the migration there:

```bash
python3 "$IDH_ROOT/scripts/smelt_migrate.py" "$PROJECT" "${REFERENCES[@]}"
```

After success, read its versioned `memory/SMELT.md`. If that prompt or the
project convention is missing, report it and stop. Already migrated projects
are a no-op. Report/journal bytes and provenance remain preserved; review all
migration edits before committing. There is no old command alias, compatibility
symlink or old-format consolidation branch.

## Three main functions

Apply these to consolidated `memory/topics/` and the index:

- **Pruning:** remove outdated, irrelevant or superseded information from the
  current memory. Record the reason and retained source references in the report.
- **Merging:** combine duplicate or overlapping entries into one accurate record,
  preserving source links, conditions, exceptions and unresolved contradictions.
  Carry quotations from manuscript sources, verified on the page, and their
  locators (page, folio, note number) verbatim into topics; never paraphrase,
  condense or merge them away. Keep conflicting recorded locators as an
  unresolved contradiction. Operational memory is condensed freely.
- **Refreshing:** update stale context that remains relevant using current
  evidence; flag uncertainty when it cannot be verified.

The raw journal stays append-only. Pruning a consolidated claim never deletes
its source experience. One carve-out: legacy review-attribution records move
once, by `git mv` with their bytes intact, to `memory/evidence/attribution/`.
`memory/MEMORY.md` has **at most 40 lines**, counting headings and blank
lines. Keep details in the journal, linked from the department page, rather
than expanding the index.

A topic is the as-built guide to one department (current claims, each linked
to its journal episode) and holds at most 4 KB outside its Retired and Sources
sections. Details: `memory/SMELT.md` § Job of a topic and caps.

## Coherence across indexed memories and harness rules

Pay particular attention to coherence among all memories referenced by the
index, not just duplicate wording. Compare their claims, scope, conditions and
exceptions with each other and with applicable harness rules, read as authority
sources. Refreshing, merging or pruning must not leave contradictory current
advice in another indexed topic.

A memory cannot override a harness rule. Correct or withdraw conflicting
consolidated claims when the evidence and applicable rule are clear. Preserve
the factual episode and explain the change in the report. If scope, authority or
evidence is ambiguous, mark the conflict explicitly and avoid presenting either
claim as settled advice. Reading harness rules never authorizes editing them.
Do not infer a new rule from a repeated experience or manufacture agreement.

## Procedure

After the writing run's migration succeeds, continue sequentially:

1. Read `memory/MEMORY.md`, relevant `topics/`, previous accepted reports in
   `memory/smelts/` and new entries in `journal/YYYY/`. Skip
   `*review-attribution-*` files, route-grid telemetry rather than experiences
   (their home is `memory/evidence/attribution/`). Skip age-encrypted `.age`
   entries when the project key is unavailable, recording the skipped count;
   never treat a skipped or unavailable source as empty. Read native notes only
   as attributed sources when available; report unavailable sources. Native
   notes are not the canonical reference or a write destination.
2. Apply pruning, merging and refreshing to `memory/topics/`. Link source
   episodes; distinguish hypotheses from supported observations. Update the
   `memory/MEMORY.md` index within its 40-line maximum. Never rewrite, move or
   delete journal entries. Do not propose rules.
3. Write a report in `memory/smelts/` listing sources and revisions, changes,
   unresolved questions, runtime/model and prompt revision. Preserve the text of
   native notes actually used in the report or a versioned appendix, adapted to
   the project's audience. A fingerprint alone cannot preserve a mutable note.
4. Check coherence across all indexed memories and applicable harness rules,
   links, provenance, the migration/consolidation diff and the index line count.
   Reduce the index if it exceeds 40 lines before committing. Commit the
   authorized migration edits and memory outputs on the project branch and
   submit a merge request following its integration policy. Do not merge
   automatically. Preserve and report the branch if submission fails. Only
   accepted reports count as completed processing on subsequent runs.

## Encrypted entries

Uncleared material lives in the project repository as `.age` ciphertext. Smelt
uses the same pinned age commands and the same per-project key as capture —
decrypt with `age -d -i <key>`, re-encrypt with
`age -r <recipient> -o <entry>.age` — and never writes plaintext to the
working tree. Re-encryption writes a sibling temporary ciphertext and
atomically replaces the original only after success; `age -o` overwrites an
existing destination silently, so writing in place could destroy the
original mid-write. Without the key, skip `.age` entries and record the
skipped count: they are existing but unreadable, not empty. The versioned
`memory/SMELT.md` prompt defines the operational detail, including the three
failure modes: an authentication failure (key missing, unreadable or wrong)
skips and counts the entry; malformed ciphertext is left untouched and
reported unreadable; a re-encryption failure removes the temporary
ciphertext, keeps the original entry and reports that the consolidation is
not done. Never leave plaintext or a partial ciphertext in the tree.

## Authority and invocation

The explicit invocation authorizes the migration helper's one-way path moves
and mechanical path/command substitutions in the prompt, index, topics and
inventoried active references, including the selected project's AGENTS.md.
This exception is limited to migration in its isolated branch: no policy
rewriting, rule promotion, historical-ledger edits or cross-project writes.

Consolidation writes only `memory/MEMORY.md`, `memory/topics/` and
`memory/smelts/` within the selected project repository. Uncleared material stays in that same
repository as age-encrypted `.age` ciphertext — there is no separate
companion store. It does not
modify AGENTS.md, rules, skills, runbooks or tests, open crystallisation issues,
propose promotions, or write cross-project provenance into the harness.
Crystallisation requires a separate explicit user request naming its scope and
destination. A useful pattern or a reviewed memory PR is not that request.

Lair completes its work and suggests smelt in its conclusion after 5 or more
new experiences. It neither waits nor launches smelt. Smelt runs when explicitly
invoked as a separate follow-up, in a new `/clear` session — a fresh context,
not the wrapping session's compacted residue.
There is no timer or automatic periodic launch. Use an isolated project checkout. Missing paths or permissions are visible
failures; never fall back to the harness or restore/change its primary branch.
