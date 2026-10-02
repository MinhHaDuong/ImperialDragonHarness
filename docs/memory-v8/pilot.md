# Memory v8 pilot declaration (ticket 0920)

Activated 2026-10-02 by the author's batched decisions, recorded in the 0920
ticket log. This document declares the pilot's audience and companion policy
for author review. Its only runtime change is the SessionStart index injection
becoming project-scoped (see Rollback below).

## Pilot project

The harness repository itself, per the candidate named in the
[source inventory](source-inventory.md). Initial sources are limited to the
ten `memory/` root files inventoried there. No `projects/*` export is pooled
into harness memory. Each imported source keeps its provenance — per-file
revisions are in [source-revisions.tsv](source-revisions.tsv) — its original
text stays accessible, and originals are not rewritten.

## Audience

The public repository carries the themes (`memory/topics/`), the factual
journal (`memory/journal/YYYY/`) and the reference notes. Every pilot source
was already tracked in this public repository before the pilot; none was
newly disclosed by it. Material not cleared for the public audience never
enters the public repository — an ignored directory or a public branch is
insufficient as private storage.

## Private companion (declared, not created)

Uncleared material belongs in a versioned private companion store with its
own access and versioning convention. Concrete arrangement proposed in the
0920 merge request for author review; this pilot creates no companion and
invents no content for it. Nothing currently awaits that audience.

## Rollback and old-path correspondence

Rollback is reverting this PR's merge: the legacy index and the
cross-project hook injection remain in Git history. Every path the legacy
index linked is still linked from the v8 surface at its original location.
The journal is append-only; no entry was moved or rewritten. No other
project's setup changed — this declaration covers only this repository
(no global rollout; 0913 retains the rollout).

## Reading

The v8 reading section is merged into this repository's `AGENTS.md`
(see [templates/AGENTS.md](templates/AGENTS.md)), abridged to fit the
resident-census import budget by dropping or shortening clauses; diff the
section against the template for the exact differences. DREAM.md versioning
belongs to 0916, not to this pilot.
