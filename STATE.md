# Imperial Dragon Harness — State

Last updated: 2026-10-01T20:59Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T20:59Z · as of 5acab7c0 -->

**Tickets:** 24 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** 1 open PR (1 draft), oldest #1091 0d · CI main: success
**Recent (first-parent):**
  5acab7c0 Merge remote-tracking branch 'origin/main' into review-1091-split
  205b3094 Split memory helpers from portable registration and resolve review blockers
  6014c42f docs: record portable registration validation on tracker 0999

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning and documentation landed in PRs #1089/#1090. PR #1091 now owns runtime registration, launch guards and safe operator docs (child 1003). Dream/provenance changes are preserved on handoff-portable-memory for the parallel memory session (child 1002); their independent-profile commit defect is not solved here. Parent 0999 remains open for integration review.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Finish the #1091 registration gate, then continue 1002 in the memory session. Native packaging and opt-in shell/timer integration remain future work.
Memory v7 starts with 0911 and 0917; 0920/0923 now use the portable root contract.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
