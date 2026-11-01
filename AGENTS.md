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

Tickets: `tickets/*.erg`, also the channel between projects (`rules/guards.md`).
A GitHub Issue, if any, only points to a ticket.

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

When the harness itself is the explicitly assigned project, its own project
memory follows the policy every project follows: the boundary in
`rules/guards.md`, capture in `skills/roar`, consolidation in `skills/smelt`,
crystallisation in `skills/brood`.
