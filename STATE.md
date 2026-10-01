# Imperial Dragon Harness — State

Last updated: 2026-10-01T21:03Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T21:03Z · as of fd5d9a64 -->

**Tickets:** 22 ready · 21 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** 1 open PR (1 draft), oldest #1091 0d · CI main: success
**Recent (first-parent):**
  fd5d9a64 Merge parallel memory v8, AGENTS entrypoint and scheduler removal
  daf55488 Renumber registration child after parallel ticket allocation
  11b755ce Preserve pre-existing resources in registration and repair guidance

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning and documentation landed in PRs #1089/#1090. PR #1091 merged runtime registration, launch guards and safe operator docs (closed child 1003). Child 1002 is WONTDO, superseded by memory v8; its handoff patch is historical and unapproved. 0934 retires the unused provenance helper and its dedicated tests while preserving all source data. Parent 0999 remains open for integration review.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Review 0999 integration after registration child 1003 landed; do not implement the closed legacy handoff 1002. Native packaging and opt-in shell integration remain; scheduling is external.
Memory v8 is drafted: repository Markdown, factual roar capture and dream suggested by lair after five new experiences.
Start with 0911/0917, then pilot 0920; capture 0988 and prompt/follow-up suggestion 0916/0910 follow.
The old library/compiler/loader train is superseded; runtime behaviour is unchanged.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
