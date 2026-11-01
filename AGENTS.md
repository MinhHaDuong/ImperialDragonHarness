<!-- Scope: this file is the harness repository's own bylaws, read only when a
session works on the harness itself. Law for every project lives in rules/:
four resident files (workflow.md, git.md, claude-code.md, guards.md) load in
every Claude Code session (Codex and Pi load none yet, ticket 1413), the others when a session touches matching files (paths:).
Each research project keeps its own AGENTS.md.
Policy here that binds all projects belongs in rules/ or a skill (ticket 1412). -->
# Harness agent profiles

Worker choice (model, effort, reviewer decorrelation) is made by the route skill,
`skills/route/SKILL.md`, not by skills or this file. A skill states a role and a
need; it never names a model or a capability tier.

Reviewer routing and independence: `rules/workflow.md` (Delegation) and
`skills/route/references/decorrelation.md`. Record the reviewer identity, route,
evidence, and any unavailable perspective.

## Harness instructions

Guards every agent: rules/guards.md.

Current status, blockers, next actions: `STATE.md`.

Tickets: `tickets/*.erg`. GitHub Issues are for cross-repo coordination only.

Design history (memos, audits, review records): `conception/`, as in the
research projects. `docs/` is git-ignored staging for external documents
(rules/zotero.md).

## Project memory

Read [memory/MEMORY.md](memory/MEMORY.md) at task start when it exists. Open
relevant themes before acting; search themes and the journal with `rg` or
`grep` when recall is needed, and again if the task changes materially.
Missing memory does not block work; report a known incomplete installation.

## Skills catalog

The skills catalog in `skills-catalog.md` is auto-generated from `skills/*/SKILL.md` frontmatter; private skill symlinks are excluded.

A `description:` sentence starting with `Not for`, `Use for`, `Use to` or
`Keyword(s):` is a routing hint for the model; the catalog omits it.

Set each skill’s `metadata.category` frontmatter to a key in
`scripts/gen_skills_catalog.py`; an optional numeric `metadata.order` sets
its row within the section, rows without one following alphabetically. After changing a skill’s name, description,
category or order, or adding or removing a skill, run `make skills-catalog`.
`make check-skills-drift` checks the whole generated document, order included.

## Agent profiles

Profile contracts live in `profiles/<name>/PROFILE.md`; shells point to them.

Each profile declares the tools it needs on one line under its title,
`Requires-tools: Read, Bash, Skill` (comma-separated tool names, exactly one
such line). `tests/test_profile_tool_grants.py` requires the declaration to be a
subset of the `tools:` grant in `agents/<name>.md`, and a profile whose shell
lacks `Skill` to contain no `Skill(` call. The test reads only this line; it
does not parse prose, so a new tool need is declared, not written around.

For ticket operations, read and follow [tickets/AGENTS.md](tickets/AGENTS.md).
For shell tooling conventions, read and follow [RTK.md](RTK.md).

## Project memory boundary

Project experiences and consolidated memories belong only in that project's
repository; uncleared material stays encrypted. When the harness itself is
the explicitly assigned project, its own project memory follows the same
convention.

Roar records significant facts only. Smelt consolidates project memory only.
Neither proposes or creates rules, edits AGENTS.md, or promotes experiences into
instructions. Crystallisation is a separate task requiring an explicit user
request, including the intended destination. Repetition, general usefulness and
acceptance of a memory PR do not grant that authorization. Explicit Brood may
implement project improvements; a named harness receives nominations only,
until separately authorized implementation.

At Roar, commit significant facts; do not derive lessons. Smelt prunes, merges
and refreshes themes while preserving sources. Journal entries remain
append-only; link corrections from new entries. Review-attribution records
live in `memory/evidence/attribution/`, outside the journal. Keep MEMORY.md at most
40 lines; no automatic rule proposals or timer.

On explicit Smelt invocation, one-way migration may mechanically update
inventoried active path/command references in the selected project's isolated
branch, including AGENTS.md. This grants no policy changes or consolidation
writes outside memory.
