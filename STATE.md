# Imperial Dragon Harness — State

Last updated: 2026-10-01T19:52Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T19:52Z · as of 8fce5703 -->

**Tickets:** 22 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** 1 open PR, oldest #1090 0d · CI main: in progress
**Recent (first-parent):**
  8fce5703 docs: preserve checkout commands after guard test changes directory
  8c610d07 docs: simplify guides around portable agents checkout
  9cff8d73 Merge pull request #1089 from MinhHaDuong/plan-portable-agents

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning and documentation landed in PRs #1089/#1090. PR #1091 now owns runtime registration, launch guards and safe operator docs (child 1001). Dream/provenance changes are preserved on handoff-portable-memory for the parallel memory session (child 1002); their independent-profile commit defect is not solved here. Parent 0999 remains open for integration review.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Finish the #1091 registration gate, then continue 1002 in the memory session. Native packaging and opt-in shell/timer integration remain future work.
Memory v7 starts with 0911 and 0917; 0920/0923 now use the portable root contract.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
