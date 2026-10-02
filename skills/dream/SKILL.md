---
name: dream
description: "Consolidate one project's repository memory without proposing rules."
user-invocable: true
---

# Dream — project memory consolidation

Use `/dream <project-repository> [--dry-run]`. The project repository is the
write destination; the installed skill directory is never a destination.
Read its AGENTS.md and versioned `memory/DREAM.md`. If the repository, memory
convention or prompt is missing, report what is missing and stop. Do not create
a replacement store in the harness or use the legacy helper scripts: those
helpers target the old shared/native store and are not this workflow.

## Three main functions

Apply these to consolidated `memory/topics/` and the index:

- **Pruning:** remove outdated, irrelevant or superseded information from the
  current memory. Record the reason and retained source references in the report.
- **Merging:** combine duplicate or overlapping entries into one accurate record,
  preserving source links, conditions, exceptions and unresolved contradictions.
- **Refreshing:** update stale context that remains relevant using current
  evidence; flag uncertainty when it cannot be verified.

The raw journal stays append-only. Pruning a consolidated claim never deletes
its source experience. `memory/MEMORY.md` has **at most 100 lines**, counting
headings and blank lines. Keep details in topics rather than expanding the index.

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

1. Read `memory/MEMORY.md`, relevant `topics/`, previous accepted dream reports
   and new entries in `journal/YYYY/`. Skip age-encrypted `.age` entries when
   the project key is unavailable, recording the skipped count in the report;
   never treat a skipped or unavailable source as empty. Read native notes only
   as attributed sources when available; report unavailable sources. Native
   notes are not the canonical reference or a write destination.
2. In dry-run mode, report candidate thematic updates and contradictions, then
   stop without writes, branches or commits. Do not propose rules.
3. For a writing run, use an isolated project checkout and dedicated branch;
   leave the primary checkout and unrelated changes alone. Apply pruning, merging and refreshing to `memory/topics/`. Link source
   episodes; distinguish hypotheses from supported observations. Update the
   `memory/MEMORY.md` index within its 100-line maximum. Never rewrite, move or delete journal entries.
4. Write a report in `memory/dreams/` listing sources and revisions, changes,
   unresolved questions, runtime/model and prompt revision. Preserve the text of
   native notes actually used in the report or a versioned appendix, adapted to
   the project's audience. A fingerprint alone cannot preserve a mutable note.
5. Check coherence across all indexed memories and applicable harness rules,
   links, provenance, the diff and the index line count. Reduce the
   index if it exceeds 100 lines before committing. Commit only memory outputs on the
   project branch and submit a PR following its integration policy. Do not
   merge automatically. Preserve and report the branch if submission fails.
   Only accepted reports count as completed processing on subsequent runs.

## Encrypted entries

Uncleared material lives in the project repository as `.age` ciphertext. Dream
uses the same pinned age commands and the same per-project key as capture —
decrypt with `age -d -i <key>`, re-encrypt with
`age -r <recipient> -o <entry>.age` — and never writes plaintext to the
working tree. Re-encryption writes a sibling temporary ciphertext and
atomically replaces the original only after success; `age -o` overwrites an
existing destination silently, so writing in place could destroy the
original mid-write. Without the key, skip `.age` entries and record the
skipped count: they are existing but unreadable, not empty. The versioned
`memory/DREAM.md` prompt defines the operational detail, including the three
failure modes: an authentication failure (key missing, unreadable or wrong)
skips and counts the entry; malformed ciphertext is left untouched and
reported unreadable; a re-encryption failure removes the temporary
ciphertext, keeps the original entry and reports that the consolidation is
not done. Never leave plaintext or a partial ciphertext in the tree.

## Authority and invocation

Dream writes only `memory/MEMORY.md`, `memory/topics/` and `memory/dreams/`
within the project repository. Uncleared material stays in that same
repository as age-encrypted `.age` ciphertext — there is no separate
companion store. It does not
modify AGENTS.md, rules, skills, runbooks or tests, open crystallisation issues,
propose promotions, or write cross-project provenance into the harness.
Crystallisation requires a separate explicit user request naming its scope and
destination. A useful pattern or a reviewed memory PR is not that request.

Lair completes its work and suggests dream in its conclusion after 5 or more
new experiences. It neither waits nor launches dream. Dream runs when explicitly
invoked as a separate follow-up.
There is no timer or automatic periodic launch. Use an isolated project checkout. Missing paths or permissions are visible
failures; never fall back to the harness or restore/change its primary branch.
