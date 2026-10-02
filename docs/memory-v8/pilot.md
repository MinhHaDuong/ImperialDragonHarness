# Memory v8 pilot declaration (ticket 0920)

Activated 2026-10-02 by the author's batched decisions, recorded in the 0920
ticket log. This document declares the pilot's audience and private-material
policy for author review. Its only runtime change is the SessionStart index injection
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
newly disclosed by it. Author decision of 2026-10-02: material not cleared
for the public audience enters the repository only as ciphertext, never
plaintext — an ignored directory or a public branch remains insufficient
as private storage.

## Private material (encrypted in-repo, author decision 2026-10-02)

The separate private companion proposed in the 0920 merge request is
superseded; the author accepted the encrypted-in-repo costs. Uncleared
journal entries and themes are committed in this repository as `age`
ciphertext from birth (`.age` suffix); plaintext is never written to the
working tree. The key lives in `~/.config/keys` outside the repository,
is never tracked and is not named by repository content. Without the key
an entry is existing but unreadable; DREAM skips `.age` files and reports
the skipped count rather than treating them as empty. Filenames of
encrypted entries remain public metadata, and ciphertext-at-rest means a
future key leak decrypts everything ever pushed, retroactively — the
policy holds only as long as the key stays secret. Nothing currently
awaits that audience.

The concrete mechanics are pinned in [README.md](README.md) § Audience and
source handling (ticket 0988): the audience is judged at capture, before the
first byte is written; not-cleared entries are piped from stdin straight into
`age`; the per-project key is derived from the repository's own origin URL
under `~/.config/keys/memory/`, created on first private capture and never
tracked. `scripts/memory-capture.sh` is the harness's implementation.

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
