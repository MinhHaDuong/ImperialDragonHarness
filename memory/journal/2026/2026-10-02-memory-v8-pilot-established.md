# Memory v8 pilot established

Ticket 0920 resumed detached on 2026-10-02 after the author answered the
batched decision list. Three decisions were recorded in the ticket log: the
pilot project is this harness repository itself, per the candidate named in
the source inventory; the audience is the public repository for themes and
journal, with a declared versioned private companion (proposed for review,
not created) for material not cleared for that audience; and the initial
sources are only the ten `memory/` root files inventoried by 0917 — no
pooling of `projects/*` exports.

The pilot replaced the legacy cross-project index with the v8 project-local
one, added five themes with per-source provenance, and merged the v8 reading
section into AGENTS.md. Every inventoried source stayed at its original path,
unrewritten; the legacy index remains recoverable in Git history, and each
path it linked is still linked. The SessionStart hook stopped injecting the
harness index into unrelated projects' sessions — the cross-project channel
the PR #1102 review had flagged — and now injects it only where the session's
project is this repository or one of its worktrees. The resident census hook
budget was raised accordingly, from 500 to 2100 chars.

A mechanical relocated-clone test now proves the first exit criterion:
`tests/test_memory_v8_pilot.py` clones the repository, moves the clone
elsewhere, drops its origin remote, and reads the whole memory surface
through relative links alone — no original home, no harness installation.
Rollback is reverting this PR's merge; no other project's setup changed
(no global rollout).

Evidence: ticket
[tickets/closed/0920-pilot-portable-project-memory-and-shared-snapshot.erg](../../tickets/closed/0920-pilot-portable-project-memory-and-shared-snapshot.erg)
(decisions of 2026-10-02 in its log); [pilot declaration](../../docs/memory-v8/pilot.md);
[source inventory](../../docs/memory-v8/source-inventory.md); PR #1109.
