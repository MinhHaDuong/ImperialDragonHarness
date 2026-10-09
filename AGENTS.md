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

## Project memory

Read [memory/MEMORY.md](memory/MEMORY.md) at task start when it exists. Open
relevant themes before acting; search themes and the journal with `rg` or
`grep` when recall is needed, and again if the task changes materially.
Missing memory does not block work; report a known incomplete installation.

At roar, commit significant facts here; uncleared material only as encrypted `.age`;
preserve journal entries and link corrections from new entries. Do not derive
lessons, propose rules, or write into the harness for another project; DREAM
separately prunes, merges and refreshes themes, preserving sources. MEMORY.md
is at most 100 lines; no automatic rule proposals or timer.

## Skills Catalog

The skills catalog in `README.md` is auto-generated from `skills/*/SKILL.md` frontmatter.

**When you add, rename, or remove a skill:**

```bash
make skills-catalog    # Regenerate README.md catalog
```

**To detect drift:**

```bash
make check-skills-drift  # Fails if README.md is out of sync
```


## Agent profiles

Profile contracts live in `profiles/<name>/PROFILE.md`; shells point to them.

For ticket operations, read and follow [tickets/AGENTS.md](tickets/AGENTS.md).
For shell tooling conventions, read and follow [RTK.md](RTK.md).

## Project memory boundary

Project experiences and consolidated memories belong only in that project's
repository; uncleared material stays encrypted. When the harness itself is
the explicitly assigned project, its own project memory follows the same
convention.

Roar records significant facts only. Dream consolidates project memory only.
Neither proposes or creates rules, edits AGENTS.md, or promotes experiences into
instructions. Crystallisation is a separate task requiring an explicit user
request, including the intended destination. Repetition, general usefulness and
acceptance of a memory PR do not grant that authorization. Explicit Brood may
implement project improvements; a named harness receives nominations only,
until separately authorized implementation. Sources remain append-only.
